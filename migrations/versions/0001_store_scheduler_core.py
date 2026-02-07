"""0001_store_scheduler_core

Revision ID: 0001_store_scheduler_core
Revises:
Create Date: 2026-02-06 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_store_scheduler_core"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "store",
        sa.Column("store_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("store_id", name="pk_store"),
    )

    op.create_table(
        "store_room",
        sa.Column("store_room_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.store_id"], name="fk_store_room_store_id"),
        sa.PrimaryKeyConstraint("store_room_id", name="pk_store_room"),
        sa.UniqueConstraint("store_id", "name", name="uq_store_room_store_id_name"),
    )
    op.create_index("ix_store_room_store_id", "store_room", ["store_id"], unique=False)

    op.create_table(
        "script",
        sa.Column("script_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("estimated_minutes > 0", name="ck_script_estimated_minutes_positive"),
        sa.PrimaryKeyConstraint("script_id", name="pk_script"),
        sa.UniqueConstraint("name", name="uq_script_name"),
    )

    op.create_table(
        "store_script",
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("script_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["script_id"], ["script.script_id"], name="fk_store_script_script_id"),
        sa.ForeignKeyConstraint(["store_id"], ["store.store_id"], name="fk_store_script_store_id"),
        sa.PrimaryKeyConstraint("store_id", "script_id", name="pk_store_script"),
    )
    op.create_index("ix_store_script_script_id", "store_script", ["script_id"], unique=False)
    op.create_index("ix_store_script_store_id_active", "store_script", ["store_id", "is_active"], unique=False)

    op.create_table(
        "script_character",
        sa.Column("character_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("script_id", sa.BigInteger(), nullable=False),
        sa.Column("character_name", sa.Text(), nullable=False),
        sa.Column(
            "is_dm",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["script_id"],
            ["script.script_id"],
            name="fk_script_character_script_id",
        ),
        sa.PrimaryKeyConstraint("character_id", name="pk_script_character"),
        sa.UniqueConstraint("script_id", "character_name", name="uq_script_character_script_id_name"),
    )
    op.create_index("ix_script_character_script_id", "script_character", ["script_id"], unique=False)

    op.create_table(
        "dm",
        sa.Column("dm_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("dm_id", name="pk_dm"),
    )

    op.create_table(
        "dm_store_membership",
        sa.Column("dm_id", sa.BigInteger(), nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["dm_id"],
            ["dm.dm_id"],
            name="fk_dm_store_membership_dm_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["store.store_id"],
            name="fk_dm_store_membership_store_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("dm_id", "store_id", name="pk_dm_store_membership"),
    )
    op.create_index(
        "ix_dm_store_membership_store_id",
        "dm_store_membership",
        ["store_id"],
        unique=False,
    )

    op.create_table(
        "client",
        sa.Column("client_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("client_id", name="pk_client"),
    )
    op.create_index("ix_client_display_name", "client", ["display_name"], unique=False)

    op.create_table(
        "slot",
        sa.Column("slot_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.store_id"], name="fk_slot_store_id"),
        sa.PrimaryKeyConstraint("slot_id", name="pk_slot"),
        sa.UniqueConstraint("store_id", "start_at", name="uq_slot_store_id_start_at"),
    )
    op.create_index("ix_slot_store_id", "slot", ["store_id"], unique=False)
    op.create_index("ix_slot_store_id_start_at", "slot", ["store_id", "start_at"], unique=False)

    op.create_table(
        "booking_status",
        sa.Column("booking_status_id", sa.SmallInteger(), nullable=False),
        sa.Column("booking_status_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("booking_status_id", name="pk_booking_status"),
        sa.UniqueConstraint("booking_status_name", name="uq_booking_status_name"),
    )
    op.execute(
        """
        INSERT INTO booking_status (booking_status_id, booking_status_name)
        VALUES
            (1, 'incomplete'),
            (2, 'scheduled'),
            (3, 'cancelled'),
            (4, 'completed');
        """
    )

    op.create_table(
        "booking",
        sa.Column("booking_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("script_id", sa.BigInteger(), nullable=False),
        sa.Column("slot_id", sa.BigInteger(), nullable=True),
        sa.Column("store_room_id", sa.BigInteger(), nullable=True),
        sa.Column("booking_status_id", sa.SmallInteger(), nullable=False),
        sa.Column("target_month", sa.Date(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_override_minutes", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "duration_override_minutes IS NULL OR duration_override_minutes > 0",
            name="ck_booking_duration_override_minutes_positive",
        ),
        sa.CheckConstraint(
            "target_month IS NULL OR target_month = date_trunc('month', target_month)::date",
            name="ck_booking_target_month_first_day",
        ),
        sa.CheckConstraint(
            "start_at IS NULL OR end_at IS NULL OR end_at > start_at",
            name="ck_booking_end_after_start",
        ),
        sa.CheckConstraint(
            """
            (
              booking_status_id = 1
              AND target_month IS NOT NULL
              AND start_at IS NULL
              AND end_at IS NULL
              AND slot_id IS NULL
              AND store_room_id IS NULL
            ) OR (
              booking_status_id IN (2, 4)
              AND target_month IS NULL
              AND start_at IS NOT NULL
              AND end_at IS NOT NULL
              AND slot_id IS NOT NULL
              AND store_room_id IS NOT NULL
            ) OR (
              booking_status_id = 3
              AND (
                (
                  target_month IS NOT NULL
                  AND start_at IS NULL
                  AND end_at IS NULL
                  AND slot_id IS NULL
                  AND store_room_id IS NULL
                ) OR (
                  target_month IS NULL
                  AND start_at IS NOT NULL
                  AND end_at IS NOT NULL
                  AND slot_id IS NOT NULL
                  AND store_room_id IS NOT NULL
                )
              )
            )
            """,
            name="ck_booking_state_shape",
        ),
        sa.ForeignKeyConstraint(
            ["booking_status_id"],
            ["booking_status.booking_status_id"],
            name="fk_booking_booking_status_id",
        ),
        sa.ForeignKeyConstraint(["client_id"], ["client.client_id"], name="fk_booking_client_id"),
        sa.ForeignKeyConstraint(["script_id"], ["script.script_id"], name="fk_booking_script_id"),
        sa.ForeignKeyConstraint(["slot_id"], ["slot.slot_id"], name="fk_booking_slot_id"),
        sa.ForeignKeyConstraint(
            ["store_id", "script_id"],
            ["store_script.store_id", "store_script.script_id"],
            name="fk_booking_store_script",
        ),
        sa.ForeignKeyConstraint(
            ["store_room_id"],
            ["store_room.store_room_id"],
            name="fk_booking_store_room_id",
        ),
        sa.ForeignKeyConstraint(["store_id"], ["store.store_id"], name="fk_booking_store_id"),
        sa.PrimaryKeyConstraint("booking_id", name="pk_booking"),
    )
    op.create_index(
        "ix_booking_store_status_id",
        "booking",
        ["store_id", "booking_status_id"],
        unique=False,
    )
    op.create_index("ix_booking_store_target_month", "booking", ["store_id", "target_month"], unique=False)
    op.create_index("ix_booking_store_room_start_at", "booking", ["store_room_id", "start_at"], unique=False)
    op.create_index("ix_booking_store_room_end_at", "booking", ["store_room_id", "end_at"], unique=False)
    op.create_index("ix_booking_slot_id", "booking", ["slot_id"], unique=False)

    op.create_table(
        "booking_dm_assignment",
        sa.Column(
            "booking_dm_assignment_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("dm_id", sa.BigInteger(), nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["booking.booking_id"],
            name="fk_booking_dm_assignment_booking_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["script_character.character_id"],
            name="fk_booking_dm_assignment_character_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["dm_id"],
            ["dm.dm_id"],
            name="fk_booking_dm_assignment_dm_id",
        ),
        sa.PrimaryKeyConstraint("booking_dm_assignment_id", name="pk_booking_dm_assignment"),
    )
    op.create_index(
        "ix_booking_dm_assignment_booking_id",
        "booking_dm_assignment",
        ["booking_id"],
        unique=False,
    )
    op.create_index(
        "ix_booking_dm_assignment_dm_id",
        "booking_dm_assignment",
        ["dm_id"],
        unique=False,
    )
    op.create_index(
        "uq_booking_dm_assignment_booking_character",
        "booking_dm_assignment",
        ["booking_id", "character_id"],
        unique=True,
        postgresql_where=sa.text("character_id IS NOT NULL"),
    )
    op.create_index(
        "uq_booking_dm_assignment_booking_dm_free",
        "booking_dm_assignment",
        ["booking_id", "dm_id"],
        unique=True,
        postgresql_where=sa.text("character_id IS NULL"),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_booking_end_at()
        RETURNS trigger AS $$
        DECLARE
            effective_minutes integer;
        BEGIN
            IF NEW.start_at IS NULL THEN
                NEW.end_at := NULL;
                RETURN NEW;
            END IF;

            SELECT COALESCE(NEW.duration_override_minutes, s.estimated_minutes)
              INTO effective_minutes
              FROM script AS s
             WHERE s.script_id = NEW.script_id;

            IF effective_minutes IS NULL OR effective_minutes <= 0 THEN
                RAISE EXCEPTION 'Unable to compute booking end_at for script_id=%', NEW.script_id;
            END IF;

            NEW.end_at := NEW.start_at + make_interval(mins => effective_minutes);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_booking_set_end_at
        BEFORE INSERT OR UPDATE OF script_id, start_at, duration_override_minutes
        ON booking
        FOR EACH ROW
        EXECUTE FUNCTION set_booking_end_at();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION enforce_booking_dm_store_scope()
        RETURNS trigger AS $$
        DECLARE
            v_booking_store_id bigint;
        BEGIN
            SELECT store_id
              INTO v_booking_store_id
              FROM booking
             WHERE booking_id = NEW.booking_id;

            IF v_booking_store_id IS NULL THEN
                RAISE EXCEPTION 'booking_id % does not exist', NEW.booking_id;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM dm_store_membership AS dsm
                WHERE dsm.dm_id = NEW.dm_id
                  AND dsm.store_id = v_booking_store_id
            ) THEN
                RAISE EXCEPTION
                    'dm_id % is not a member of booking store_id %',
                    NEW.dm_id,
                    v_booking_store_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_booking_dm_assignment_enforce_store_scope
        BEFORE INSERT OR UPDATE OF booking_id, dm_id
        ON booking_dm_assignment
        FOR EACH ROW
        EXECUTE FUNCTION enforce_booking_dm_store_scope();
        """
    )

    op.execute(
        """
        DO $$
        DECLARE
            v_demo_store_id bigint;
            v_partner_store_id bigint;
            v_demo_room_a_id bigint;
            v_partner_room_1_id bigint;
            v_script_haunted_id bigint;
            v_script_midnight_id bigint;
            v_char_host_id bigint;
            v_char_suspect_id bigint;
            v_char_conductor_id bigint;
            v_dm_ava_id bigint;
            v_dm_ben_id bigint;
            v_dm_cara_id bigint;
            v_dm_devin_id bigint;
            v_client_alex_id bigint;
            v_client_jordan_id bigint;
            v_client_morgan_id bigint;
            v_slot_demo_1800_id bigint;
            v_slot_demo_1900_id bigint;
            v_slot_partner_1800_id bigint;
            v_booking_demo_1800_id bigint;
            v_booking_demo_1900_id bigint;
            v_booking_partner_1800_id bigint;
        BEGIN
            INSERT INTO store (name) VALUES ('MVP Demo Store') RETURNING store_id INTO v_demo_store_id;
            INSERT INTO store (name) VALUES ('MVP Partner Store') RETURNING store_id INTO v_partner_store_id;

            INSERT INTO store_room (store_id, name) VALUES (v_demo_store_id, 'Room A')
            RETURNING store_room_id INTO v_demo_room_a_id;
            INSERT INTO store_room (store_id, name) VALUES (v_demo_store_id, 'Room B');
            INSERT INTO store_room (store_id, name) VALUES (v_partner_store_id, 'Partner Room 1')
            RETURNING store_room_id INTO v_partner_room_1_id;

            INSERT INTO script (name, estimated_minutes)
            VALUES ('Haunted Mansion', 180)
            RETURNING script_id INTO v_script_haunted_id;
            INSERT INTO script (name, estimated_minutes)
            VALUES ('Midnight Train', 240)
            RETURNING script_id INTO v_script_midnight_id;

            INSERT INTO store_script (store_id, script_id, is_active)
            VALUES
                (v_demo_store_id, v_script_haunted_id, true),
                (v_demo_store_id, v_script_midnight_id, true),
                (v_partner_store_id, v_script_haunted_id, true),
                (v_partner_store_id, v_script_midnight_id, false);

            INSERT INTO script_character (script_id, character_name, is_dm)
            VALUES
                (v_script_haunted_id, 'Host', true),
                (v_script_haunted_id, 'Detective', false),
                (v_script_haunted_id, 'Suspect', true),
                (v_script_haunted_id, 'Witness', false),
                (v_script_midnight_id, 'Conductor', true),
                (v_script_midnight_id, 'Engineer', false),
                (v_script_midnight_id, 'Passenger A', false),
                (v_script_midnight_id, 'Passenger B', false),
                (v_script_midnight_id, 'Inspector', true);

            SELECT character_id INTO v_char_host_id
            FROM script_character
            WHERE script_id = v_script_haunted_id AND character_name = 'Host';

            SELECT character_id INTO v_char_suspect_id
            FROM script_character
            WHERE script_id = v_script_haunted_id AND character_name = 'Suspect';

            SELECT character_id INTO v_char_conductor_id
            FROM script_character
            WHERE script_id = v_script_midnight_id AND character_name = 'Conductor';

            INSERT INTO dm (display_name) VALUES ('DM Ava') RETURNING dm_id INTO v_dm_ava_id;
            INSERT INTO dm (display_name) VALUES ('DM Ben') RETURNING dm_id INTO v_dm_ben_id;
            INSERT INTO dm (display_name) VALUES ('DM Cara') RETURNING dm_id INTO v_dm_cara_id;
            INSERT INTO dm (display_name) VALUES ('DM Devin') RETURNING dm_id INTO v_dm_devin_id;

            INSERT INTO dm_store_membership (dm_id, store_id)
            VALUES
                (v_dm_ava_id, v_demo_store_id),
                (v_dm_ben_id, v_demo_store_id),
                (v_dm_cara_id, v_demo_store_id),
                (v_dm_devin_id, v_demo_store_id),
                (v_dm_ava_id, v_partner_store_id),
                (v_dm_devin_id, v_partner_store_id);

            INSERT INTO client (display_name, phone)
            VALUES ('Alex Chen', '555-0101')
            RETURNING client_id INTO v_client_alex_id;
            INSERT INTO client (display_name, phone)
            VALUES ('Jordan Lee', '555-0102')
            RETURNING client_id INTO v_client_jordan_id;
            INSERT INTO client (display_name) VALUES ('Taylor Kim');
            INSERT INTO client (display_name, phone)
            VALUES ('Morgan Park', '555-0201')
            RETURNING client_id INTO v_client_morgan_id;

            INSERT INTO slot (store_id, start_at)
            VALUES (v_demo_store_id, TIMESTAMPTZ '2026-03-15 18:00:00-04')
            RETURNING slot_id INTO v_slot_demo_1800_id;
            INSERT INTO slot (store_id, start_at)
            VALUES (v_demo_store_id, TIMESTAMPTZ '2026-03-15 19:00:00-04')
            RETURNING slot_id INTO v_slot_demo_1900_id;
            INSERT INTO slot (store_id, start_at)
            VALUES (v_partner_store_id, TIMESTAMPTZ '2026-03-16 18:00:00-04')
            RETURNING slot_id INTO v_slot_partner_1800_id;

            INSERT INTO booking (
                store_id,
                client_id,
                script_id,
                slot_id,
                store_room_id,
                booking_status_id,
                start_at
            )
            VALUES (
                v_demo_store_id,
                v_client_alex_id,
                v_script_haunted_id,
                v_slot_demo_1800_id,
                v_demo_room_a_id,
                2,
                TIMESTAMPTZ '2026-03-15 18:00:00-04'
            )
            RETURNING booking_id INTO v_booking_demo_1800_id;

            INSERT INTO booking (
                store_id,
                client_id,
                script_id,
                slot_id,
                store_room_id,
                booking_status_id,
                start_at,
                duration_override_minutes
            )
            VALUES (
                v_demo_store_id,
                v_client_jordan_id,
                v_script_midnight_id,
                v_slot_demo_1900_id,
                v_demo_room_a_id,
                2,
                TIMESTAMPTZ '2026-03-15 19:00:00-04',
                210
            )
            RETURNING booking_id INTO v_booking_demo_1900_id;

            INSERT INTO booking (
                store_id,
                client_id,
                script_id,
                booking_status_id,
                target_month
            )
            VALUES (
                v_demo_store_id,
                v_client_alex_id,
                v_script_midnight_id,
                1,
                DATE '2026-04-01'
            );

            INSERT INTO booking (
                store_id,
                client_id,
                script_id,
                slot_id,
                store_room_id,
                booking_status_id,
                start_at
            )
            VALUES (
                v_partner_store_id,
                v_client_morgan_id,
                v_script_haunted_id,
                v_slot_partner_1800_id,
                v_partner_room_1_id,
                2,
                TIMESTAMPTZ '2026-03-16 18:00:00-04'
            )
            RETURNING booking_id INTO v_booking_partner_1800_id;

            INSERT INTO booking_dm_assignment (booking_id, dm_id, character_id)
            VALUES
                (v_booking_demo_1800_id, v_dm_ava_id, v_char_host_id),
                (v_booking_demo_1800_id, v_dm_ben_id, v_char_suspect_id),
                (v_booking_demo_1900_id, v_dm_cara_id, v_char_conductor_id),
                (v_booking_demo_1900_id, v_dm_ben_id, NULL),
                (v_booking_partner_1800_id, v_dm_ava_id, NULL);
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_booking_dm_assignment_enforce_store_scope ON booking_dm_assignment;")
    op.execute("DROP FUNCTION IF EXISTS enforce_booking_dm_store_scope();")
    op.execute("DROP TRIGGER IF EXISTS trg_booking_set_end_at ON booking;")
    op.execute("DROP FUNCTION IF EXISTS set_booking_end_at();")

    op.drop_table("booking_dm_assignment")
    op.drop_table("booking")
    op.drop_table("booking_status")
    op.drop_table("slot")
    op.drop_table("client")
    op.drop_table("dm_store_membership")
    op.drop_table("dm")
    op.drop_table("script_character")
    op.drop_table("store_script")
    op.drop_table("script")
    op.drop_table("store_room")
    op.drop_table("store")
