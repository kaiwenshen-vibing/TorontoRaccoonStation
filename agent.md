# agent.md — 浣熊剧本杀拼车/约档期平台（FastAPI + Postgres + Redis，容器化+自动扩缩容）


---

## 0. 结论总览（决策摘要）

- **术语（代码层）**
  - 剧本杀：`scripted_roleplay`
  - 单次活动：`session`
  - 拼车：`carpool`
  - 档期：`slot`
  - 角色位/岗位：`cast_position`
  - 报名/占位：`signup`
  - 用户锁定（最多 1–2 个）：`user_lockin`

- **技术栈**
  - 后端：**FastAPI**
  - 主库：**Postgres**（强一致、事务、约束、锁）
  - 缓存/限流/预占：**Redis**
  - 部署：**容器常驻 + 自动扩缩容**（低成本常态运行，高峰弹性扩）

- **高并发抢位原则**
  - **最终一致性/不超卖**必须由 **Postgres 事务 + 行锁（`SELECT … FOR UPDATE`）**兜底
  - Redis 只做 **预占 token、限流、热点缓存**，不当最终库存
  - 用户只能 **lock in 1–2 个**：用 `user_lockin(user_id, slot_no=1/2)` 的硬约束实现

---

## 1. 术语与文案（中英对照）

> UI 全中文；代码/接口/数据库全英文，需保持统一可读性。

### 1.1 核心术语（必须统一）
| 中文 | 代码/DB（snake_case） | 说明 |
|---|---|---|
| 剧本杀 | `scripted_roleplay` | 顶层概念（品类） |
| 剧本 | `script` | 单个剧本实体 |
| 一局/一场 | `session` | 单次活动 |
| 拼车/组局 | `carpool` | 招募/凑人/约档期模块名 |
| 档期/店家放的时间段 | `slot` | 店家发布的可预约时段 |
| cast（3–4 位） | `cast_position` | cast 岗位或名额 |
| 玩家位 | `player_capacity/taken` | session 内玩家容量 |
| 报名/占位 | `signup` | 玩家或 cast 的占位记录 |
| 锁定（最多 1–2 个） | `user_lockin` | 用户锁位上限规则的实现 |

### 1.2 类型标签（建议枚举）
- 情感本：`emotional`
- 推理本：`mystery`
- 欢乐本：`comedy`
- 机制本：`mechanics`
- 恐怖本：`horror`

---

## 2. 命名规范（强制）

### 2.1 统一规则
1. **全小写 + snake_case**
2. **实体用名词，动作用动词**
3. **ID 一律 `<entity>_id`**
4. 时间字段：时间点 `_at`，日期 `_date`，时区 `timezone`
5. 状态字段：`<entity>_status`，枚举值全部小写

### 2.2 例子
- 表：`slot`, `session`, `cast_position`, `signup`, `user_lockin`
- 字段：`start_at`, `end_at`, `created_at`, `updated_at`, `slot_status`
- 动作：`join_carpool`, `leave_carpool`, `switch_to_cast`

---

## 3. 架构与部署（容器常驻 + 自动扩缩容）

### 3.1 为什么选容器常驻（而非纯 Lambda）
- 业务核心是 **高并发写入 + 强一致事务**（抢 slot / 抢 cast）
- 传统 serverless 在高并发下容易遇到 **数据库连接爆炸**、冷启动抖动、长连接困难
- 容器常驻可以稳定使用连接池，高峰再扩容副本数，整体更省心

### 3.2 组件职责
- **FastAPI**：REST API / 权限 / 业务规则 / 事务编排
- **Postgres**：最终真相（库存、锁、唯一约束）
- **Redis**：
  - 预占 token（2 分钟）减少无效争抢
  - 限流（IP/user）保护系统
  - 缓存热点读（slot 列表、session 列表等）
- 对象存储（可选）：封面图、剧本资料等大文件

---

## 4. 核心业务：slot、session、carpool、cast 的关系

### 4.1 解释
- **slot**：店家放出来的时间段（抢的对象之一）
- **session**：把一个 slot + script 组合成“一场”
- **carpool_post**（可选/后续扩展）：拼车帖/招募帖（可以先以 session 为中心，MVP 暂不单独建 carpool_post 也可以）
- **cast_position**：每场 session 需要的 cast 岗位/名额（3–4 个）
- **signup**：用户报名记录（player 或 cast）
- **user_lockin**：限制用户同时锁定的场次 <= 2

### 4.2 两种玩法兼容
1) 玩家“抢档期”（不关心 cast）  
- 默认实现：抢 **player 位**（confirmed），后续可切换为 cast  
2) 玩家“抢确定 cast 的档期”  
- `session.cast_lock_mode='fixed'` 或 cast_position 已满  
- 只允许抢玩家位（或指定规则）

---

## 5. 数据模型（Postgres，MVP 版本）

> 下述 schema 为建议起点，满足：强一致、可扩展、命名统一。

### 5.1 slot（店家放档期）
```sql
create table slot (
  slot_id            bigserial primary key,
  store_id           bigint not null,
  start_at           timestamptz not null,
  end_at             timestamptz not null,
  timezone           text not null default 'America/Toronto',
  slot_status        text not null check (slot_status in ('open','locked','cancelled')),
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index idx_slot_store_time on slot(store_id, start_at);
```

### 5.2 session（单次活动）
```sql
create table session (
  session_id         bigserial primary key,
  slot_id            bigint not null unique references slot(slot_id),
  script_id          bigint not null,
  store_id           bigint not null,
  session_status     text not null check (session_status in ('draft','scheduled','ongoing','completed','cancelled')),
  player_capacity    int not null,
  player_taken       int not null default 0,
  cast_lock_mode     text not null check (cast_lock_mode in ('open','fixed')),
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index idx_session_store on session(store_id);
```

### 5.3 cast_position（cast 岗位/名额）
```sql
create table cast_position (
  cast_position_id   bigserial primary key,
  session_id         bigint not null references session(session_id),
  role_key           text not null,  -- e.g. 'dm', 'npc_a', 'npc_b', 'host'
  capacity           int not null default 1,
  taken              int not null default 0,
  unique(session_id, role_key)
);
```

### 5.4 signup（报名/占位）
```sql
create table signup (
  signup_id          bigserial primary key,
  session_id         bigint not null references session(session_id),
  user_id            bigint not null,
  signup_type        text not null check (signup_type in ('player','cast')),
  cast_position_id   bigint null references cast_position(cast_position_id),
  signup_status      text not null check (signup_status in ('pending','confirmed','cancelled','expired')),
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),
  unique(session_id, user_id, signup_type) -- 防重复
);

create index idx_signup_user on signup(user_id, signup_status);
```

### 5.5 user_lockin（限制用户同时 lock in <= 2）
> 用“两个槽位”强约束，不需要 trigger，事务内可安全分配。

```sql
create table user_lockin (
  user_id            bigint not null,
  slot_no            smallint not null check (slot_no in (1,2)),
  session_id         bigint not null references session(session_id),
  lock_status        text not null check (lock_status in ('active','released')),
  created_at         timestamptz not null default now(),
  released_at        timestamptz null,
  primary key(user_id, slot_no),
  unique(user_id, session_id)
);

create index idx_user_lockin_active on user_lockin(user_id) where lock_status='active';
```

---

## 6. 抢位一致性：事务与锁（关键）

### 6.1 原则
- 所有“扣库存/占位”的操作必须在 **同一个 DB 事务**中完成
- 采用 `SELECT … FOR UPDATE` 对 session 或 cast_position 行加锁
- 任何重复点击/重试都必须 **幂等**（不重复扣）

### 6.2 抢玩家位（join player）
事务步骤（伪流程）：
1. `SELECT * FROM session WHERE session_id=? FOR UPDATE`
2. 检查 `player_taken < player_capacity`
3. 对用户 lockin 加锁：`SELECT * FROM user_lockin WHERE user_id=? FOR UPDATE`
4. 找空槽位 `slot_no=1/2`：
   - 若两个槽位都 active → 拒绝（超过 lock 上限）
   - 否则插入或占用空槽位（`lock_status='active'`）
5. `UPDATE session SET player_taken = player_taken + 1 WHERE session_id=?`
6. `INSERT signup(type='player', status='confirmed') ON CONFLICT DO NOTHING`
7. commit

### 6.3 抢 cast 位（join cast）
事务步骤：
1. `SELECT session ... FOR UPDATE` 并检查 `cast_lock_mode='open'`
2. `SELECT cast_position ... FOR UPDATE` 检查 `taken < capacity`
3. lockin 分配同上
4. `UPDATE cast_position SET taken=taken+1 ...`
5. `INSERT signup(type='cast', cast_position_id=..., status='confirmed')`
6. commit

### 6.4 “只抢档期不选 cast”的处理（MVP 建议）
MVP 推荐最简单且一致：
- “只抢档期”即 **抢 player 位**（confirmed）
- 想当 cast：提供 `switch_to_cast`（一个事务内 player_taken-1 且 cast_taken+1）

后续可扩展：
- 引入 `pending`（短时 hold，不计库存）+ “确认后转 confirmed”

---

## 7. Redis 使用方式（预占 + 限流 + 缓存）

### 7.1 预占 token（推荐 120 秒）
目的：减少 DB 无效竞争、避免用户疯狂连点造成重复事务压力。

- key：`resv:{session_id}:{user_id}:{signup_type}:{cast_position_id?}`
- 操作：`SET key value NX EX 120`
- 成功：继续走 DB 事务确认
- 失败：提示“正在处理/已预占/请勿重复点击”

> 注意：Redis 预占不等于最终占位，最终结果由 DB 决定。

### 7.2 限流（保护抢位接口）
- 维度：`user_id` + `ip`
- 策略：滑动窗口/令牌桶
- 重点保护接口：
  - join player
  - join cast
  - switch role
  - store 批量放 slot（防误操作/刷接口）

### 7.3 缓存热点读
- `slot_list:{store_id}:{date_range}`
- `session_list:{store_id}:{date_range}`
- `session_detail:{session_id}`
- 注意：任何写操作后要 **主动失效**相关 key

---

## 8. API 设计轮廓（FastAPI）

> 仅提供路径建议与语义；具体鉴权/RBAC 在实现阶段细化。

### 8.1 玩家端
- `GET /sessions`（筛选：store/script/tag/time_range）
- `GET /sessions/{session_id}`
- `POST /sessions/{session_id}/join-player`
- `POST /sessions/{session_id}/join-cast`（body: `cast_position_id`）
- `POST /sessions/{session_id}/switch-to-cast`（body: `cast_position_id`）
- `POST /sessions/{session_id}/leave`
- `GET /users/me/lockins`（查看已 lock 的 1–2 个）

### 8.2 店家端（后台）
- `POST /stores/{store_id}/slots`（放档期，可批量）
- `GET /stores/{store_id}/slots`
- `POST /slots/{slot_id}/create-session`（绑定 script、设置 player_capacity、cast 结构）
- `PATCH /sessions/{session_id}`（锁 cast / 改状态）
- `GET /stores/{store_id}/sessions`

---

## 9. 身份与权限（玩家 + 店家双端）

### 9.1 基础角色
- `player`
- `store_admin`
- `dm`（可选：也可以作为 `player` 的一种能力标签）

### 9.2 多租户隔离
- 所有 store 资源必须带 `store_id`
- store_admin 只能操作自己 store 的 slot/session
- 玩家端只读 store 信息；对报名写入由 session_id 决定

---

## 10. 幂等与重试（必须）

### 10.1 幂等要求
- 同一用户对同一 session 的同类报名（player/cast）不能重复扣库存
- 依赖：
  - DB 唯一约束：`unique(session_id, user_id, signup_type)`
  - 事务内检查现有 signup
  - Redis 预占降低重复请求概率

### 10.2 客户端重试
- 建议前端传 `idempotency_key`（可选）
- 服务端可记录最近 N 分钟的 key → response（后续增强）

---

## 11. MVP 范围建议

### 11.1 必做（上线能用）
- store 放 slot
- slot 创建 session（绑定 script + 设置 player/cast）
- 玩家查看列表与详情
- 玩家抢 player 位 / 抢 cast 位
- lockin 上限（<=2）硬约束
- leave 释放库存 + 释放 lockin
- Redis 预占 + 基础限流

### 11.2 可后做（不影响核心闭环）
- carpool_post（独立拼车帖/讨论/备注）
- 投票式约档期（time_slot + vote）
- 支付/押金/违约金
- 实时推送（WebSocket/SSE）
- 搜索/推荐（ES/向量检索）

---

## 12. 关键注意事项（踩坑清单）

1. **所有扣库存必须 DB 事务完成**
2. `FOR UPDATE` 锁粒度要合理：一般锁 session 行 + 对应 cast_position 行即可
3. Redis 只作“预占与保护”，不要当最终库存
4. lockin 用两槽位模式非常稳（避免写 trigger）
5. 高峰时重点监控：
   - DB 连接数/CPU
   - Redis 命中率
   - 事务等待与死锁（必要时调整锁顺序：先 session 后 lockin 后 cast_position）

---

## 13. 下一步实现建议（工程落地）
- 使用 FastAPI + SQLAlchemy（async）或 asyncpg
- 连接池：合理配置（并发副本数 × pool size 不要打爆 Postgres）
- 迁移：Alembic
- Redis：aioredis
- 结构建议：
  - `app/models/*`（SQLAlchemy models）
  - `app/schemas/*`（Pydantic）
  - `app/services/*`（join/leave/switch 等事务服务）
  - `app/api/*`（路由）
  - `app/core/auth.py`（RBAC）

---

**本文件为平台“术语+架构+一致性”最高优先级约定。任何新增模块/表/接口必须遵循此命名与一致性原则。**
