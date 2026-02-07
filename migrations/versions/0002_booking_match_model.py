"""0002_booking_match_model

Revision ID: 0002_booking_match_model
Revises: 0001_store_scheduler_core
Create Date: 2026-02-07 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_booking_match_model"
down_revision: Union[str, Sequence[str], None] = "0001_store_scheduler_core"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "booking_client",
        sa.Column("booking_client_id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
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
            ["booking_id"],
            ["booking.booking_id"],
            name="fk_booking_client_booking_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["client.client_id"],
            name="fk_booking_client_client_id",
        ),
        sa.PrimaryKeyConstraint("booking_client_id", name="pk_booking_client"),
        sa.UniqueConstraint("booking_id", "client_id", name="uq_booking_client_booking_id_client_id"),
    )
    op.create_index("ix_booking_client_booking_id", "booking_client", ["booking_id"], unique=False)
    op.create_index("ix_booking_client_client_id", "booking_client", ["client_id"], unique=False)

    op.execute(
        """
        INSERT INTO booking_client (booking_id, client_id)
        SELECT booking_id, client_id
        FROM booking
        ON CONFLICT (booking_id, client_id) DO NOTHING;
        """
    )

    op.create_table(
        "character_client_match",
        sa.Column(
            "character_client_match_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
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
            ["booking_id"],
            ["booking.booking_id"],
            name="fk_character_client_match_booking_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["script_character.character_id"],
            name="fk_character_client_match_character_id",
        ),
        sa.ForeignKeyConstraint(
            ["client_id"],
            ["client.client_id"],
            name="fk_character_client_match_client_id",
        ),
        sa.PrimaryKeyConstraint("character_client_match_id", name="pk_character_client_match"),
        sa.UniqueConstraint(
            "booking_id",
            "character_id",
            name="uq_character_client_match_booking_character",
        ),
        sa.UniqueConstraint("booking_id", "client_id", name="uq_character_client_match_booking_client"),
    )
    op.create_index(
        "ix_character_client_match_booking_id",
        "character_client_match",
        ["booking_id"],
        unique=False,
    )

    op.create_table(
        "character_dm_match",
        sa.Column(
            "character_dm_match_id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column("booking_id", sa.BigInteger(), nullable=False),
        sa.Column("character_id", sa.BigInteger(), nullable=True),
        sa.Column("dm_id", sa.BigInteger(), nullable=False),
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
            ["booking_id"],
            ["booking.booking_id"],
            name="fk_character_dm_match_booking_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["character_id"],
            ["script_character.character_id"],
            name="fk_character_dm_match_character_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["dm_id"], ["dm.dm_id"], name="fk_character_dm_match_dm_id"),
        sa.PrimaryKeyConstraint("character_dm_match_id", name="pk_character_dm_match"),
    )
    op.create_index(
        "ix_character_dm_match_booking_id",
        "character_dm_match",
        ["booking_id"],
        unique=False,
    )
    op.create_index(
        "ix_character_dm_match_dm_id",
        "character_dm_match",
        ["dm_id"],
        unique=False,
    )
    op.create_index(
        "uq_character_dm_match_booking_character",
        "character_dm_match",
        ["booking_id", "character_id"],
        unique=True,
        postgresql_where=sa.text("character_id IS NOT NULL"),
    )
    op.create_index(
        "uq_character_dm_match_booking_dm_free",
        "character_dm_match",
        ["booking_id", "dm_id"],
        unique=True,
        postgresql_where=sa.text("character_id IS NULL"),
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION validate_character_client_match()
        RETURNS trigger AS $$
        DECLARE
            v_booking_script_id bigint;
            v_character_script_id bigint;
            v_character_is_dm boolean;
        BEGIN
            SELECT script_id
              INTO v_booking_script_id
              FROM booking
             WHERE booking_id = NEW.booking_id;

            IF v_booking_script_id IS NULL THEN
                RAISE EXCEPTION
                    'booking_id % has no script_id; set script before client matching',
                    NEW.booking_id;
            END IF;

            SELECT script_id, is_dm
              INTO v_character_script_id, v_character_is_dm
              FROM script_character
             WHERE character_id = NEW.character_id;

            IF v_character_script_id IS NULL THEN
                RAISE EXCEPTION 'character_id % does not exist', NEW.character_id;
            END IF;

            IF v_character_script_id <> v_booking_script_id THEN
                RAISE EXCEPTION
                    'character_id % does not belong to booking script_id %',
                    NEW.character_id,
                    v_booking_script_id;
            END IF;

            IF v_character_is_dm THEN
                RAISE EXCEPTION
                    'character_id % is DM-only and cannot be used in character_client_match',
                    NEW.character_id;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM booking_client AS bc
                WHERE bc.booking_id = NEW.booking_id
                  AND bc.client_id = NEW.client_id
            ) THEN
                RAISE EXCEPTION
                    'client_id % is not linked to booking_id % in booking_client',
                    NEW.client_id,
                    NEW.booking_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_character_client_match_validate
        BEFORE INSERT OR UPDATE OF booking_id, character_id, client_id
        ON character_client_match
        FOR EACH ROW
        EXECUTE FUNCTION validate_character_client_match();
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION validate_character_dm_match()
        RETURNS trigger AS $$
        DECLARE
            v_booking_script_id bigint;
            v_character_script_id bigint;
            v_character_is_dm boolean;
        BEGIN
            IF NEW.character_id IS NULL THEN
                RETURN NEW;
            END IF;

            SELECT script_id
              INTO v_booking_script_id
              FROM booking
             WHERE booking_id = NEW.booking_id;

            IF v_booking_script_id IS NULL THEN
                RAISE EXCEPTION
                    'booking_id % has no script_id; set script before character DM matching',
                    NEW.booking_id;
            END IF;

            SELECT script_id, is_dm
              INTO v_character_script_id, v_character_is_dm
              FROM script_character
             WHERE character_id = NEW.character_id;

            IF v_character_script_id IS NULL THEN
                RAISE EXCEPTION 'character_id % does not exist', NEW.character_id;
            END IF;

            IF v_character_script_id <> v_booking_script_id THEN
                RAISE EXCEPTION
                    'character_id % does not belong to booking script_id %',
                    NEW.character_id,
                    v_booking_script_id;
            END IF;

            IF NOT v_character_is_dm THEN
                RAISE EXCEPTION
                    'character_id % is non-DM and cannot be used in character_dm_match',
                    NEW.character_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_character_dm_match_validate
        BEFORE INSERT OR UPDATE OF booking_id, character_id
        ON character_dm_match
        FOR EACH ROW
        EXECUTE FUNCTION validate_character_dm_match();
        """
    )

    op.execute(
        """
        INSERT INTO character_dm_match (booking_id, dm_id, character_id, created_at)
        SELECT booking_id, dm_id, character_id, created_at
        FROM booking_dm_assignment;
        """
    )

    op.execute("DROP TRIGGER IF EXISTS trg_booking_dm_assignment_enforce_store_scope ON booking_dm_assignment;")
    op.execute(
        """
        CREATE TRIGGER trg_character_dm_match_enforce_store_scope
        BEFORE INSERT OR UPDATE OF booking_id, dm_id
        ON character_dm_match
        FOR EACH ROW
        EXECUTE FUNCTION enforce_booking_dm_store_scope();
        """
    )

    op.alter_column("booking", "script_id", existing_type=sa.BigInteger(), nullable=True)

    op.drop_constraint("ck_booking_state_shape", "booking", type_="check")
    op.create_check_constraint(
        "ck_booking_state_shape",
        "booking",
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
          AND script_id IS NOT NULL
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
              script_id IS NOT NULL
              AND target_month IS NULL
              AND start_at IS NOT NULL
              AND end_at IS NOT NULL
              AND slot_id IS NOT NULL
              AND store_room_id IS NOT NULL
            )
          )
        )
        """,
    )

    op.drop_constraint("fk_booking_client_id", "booking", type_="foreignkey")
    op.drop_column("booking", "client_id")

    op.drop_index("uq_booking_dm_assignment_booking_character", table_name="booking_dm_assignment")
    op.drop_index("uq_booking_dm_assignment_booking_dm_free", table_name="booking_dm_assignment")
    op.drop_index("ix_booking_dm_assignment_booking_id", table_name="booking_dm_assignment")
    op.drop_index("ix_booking_dm_assignment_dm_id", table_name="booking_dm_assignment")
    op.drop_table("booking_dm_assignment")


def downgrade() -> None:
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
        INSERT INTO booking_dm_assignment (booking_id, dm_id, character_id, created_at)
        SELECT booking_id, dm_id, character_id, created_at
        FROM character_dm_match;
        """
    )

    op.execute("DROP TRIGGER IF EXISTS trg_character_dm_match_enforce_store_scope ON character_dm_match;")
    op.execute(
        """
        CREATE TRIGGER trg_booking_dm_assignment_enforce_store_scope
        BEFORE INSERT OR UPDATE OF booking_id, dm_id
        ON booking_dm_assignment
        FOR EACH ROW
        EXECUTE FUNCTION enforce_booking_dm_store_scope();
        """
    )

    op.add_column("booking", sa.Column("client_id", sa.BigInteger(), nullable=True))
    op.execute(
        """
        UPDATE booking AS b
        SET client_id = x.client_id
        FROM (
            SELECT booking_id, min(client_id) AS client_id
            FROM booking_client
            GROUP BY booking_id
        ) AS x
        WHERE b.booking_id = x.booking_id;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM booking
                WHERE client_id IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade: some booking rows have no client_id candidate.';
            END IF;
        END $$;
        """
    )
    op.create_foreign_key(
        "fk_booking_client_id",
        "booking",
        "client",
        ["client_id"],
        ["client_id"],
    )
    op.alter_column("booking", "client_id", existing_type=sa.BigInteger(), nullable=False)

    op.drop_constraint("ck_booking_state_shape", "booking", type_="check")
    op.create_check_constraint(
        "ck_booking_state_shape",
        "booking",
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
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM booking
                WHERE script_id IS NULL
            ) THEN
                RAISE EXCEPTION 'Cannot downgrade: booking.script_id contains NULL values.';
            END IF;
        END $$;
        """
    )
    op.alter_column("booking", "script_id", existing_type=sa.BigInteger(), nullable=False)

    op.execute("DROP TRIGGER IF EXISTS trg_character_client_match_validate ON character_client_match;")
    op.execute("DROP FUNCTION IF EXISTS validate_character_client_match();")
    op.execute("DROP TRIGGER IF EXISTS trg_character_dm_match_validate ON character_dm_match;")
    op.execute("DROP FUNCTION IF EXISTS validate_character_dm_match();")

    op.drop_index("uq_character_dm_match_booking_character", table_name="character_dm_match")
    op.drop_index("uq_character_dm_match_booking_dm_free", table_name="character_dm_match")
    op.drop_index("ix_character_dm_match_booking_id", table_name="character_dm_match")
    op.drop_index("ix_character_dm_match_dm_id", table_name="character_dm_match")
    op.drop_table("character_dm_match")

    op.drop_index("ix_character_client_match_booking_id", table_name="character_client_match")
    op.drop_table("character_client_match")

    op.drop_index("ix_booking_client_booking_id", table_name="booking_client")
    op.drop_index("ix_booking_client_client_id", table_name="booking_client")
    op.drop_table("booking_client")
