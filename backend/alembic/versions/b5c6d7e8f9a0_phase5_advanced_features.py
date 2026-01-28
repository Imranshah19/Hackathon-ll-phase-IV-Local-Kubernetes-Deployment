"""phase5_advanced_features

Revision ID: b5c6d7e8f9a0
Revises: a1b2c3d4e5f6
Create Date: 2026-01-28 12:00:00.000000

Phase 5: Advanced Features Schema

Tables added:
- tags: User-defined task categories with colors
- task_tag: Junction table for task-tag many-to-many relationship
- recurrence_rules: Recurring task patterns (daily, weekly, monthly, yearly)
- reminders: Scheduled notifications for tasks
- task_events: Audit log for event-driven architecture

Columns added to tasks:
- priority: Task priority level (1-5, default 3)
- recurrence_rule_id: FK to recurrence_rules for recurring tasks
- parent_task_id: Self-referential FK for recurring task instances
- due: Due date/time for task

Implements:
- FR-001: Priority field with 1=Critical to 5=None scale
- FR-006: Tags with name and color per user
- FR-007: Task-tag association with junction table
- FR-013: Recurrence rules with frequency, interval, end conditions
- FR-019: Reminders with scheduled datetime
- FR-028: Task events for audit and event publishing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = 'b5c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 5 advanced features tables and columns."""

    # ==========================================================================
    # Create recurrence_rules table (must be before tasks modification)
    # ==========================================================================
    op.create_table(
        'recurrence_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('frequency', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('end_type', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False, server_default='never'),
        sa.Column('end_count', sa.Integer(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("frequency IN ('daily', 'weekly', 'monthly', 'yearly', 'custom')", name='ck_recurrence_frequency'),
        sa.CheckConstraint("end_type IN ('never', 'count', 'date')", name='ck_recurrence_end_type'),
        sa.CheckConstraint('interval >= 1', name='ck_recurrence_interval_positive'),
    )
    op.create_index(
        op.f('ix_recurrence_rules_user_id'),
        'recurrence_rules',
        ['user_id'],
        unique=False
    )

    # ==========================================================================
    # Modify tasks table: add priority, recurrence_rule_id, parent_task_id, due
    # ==========================================================================
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('tasks', sa.Column('due', sa.DateTime(), nullable=True))
    op.add_column('tasks', sa.Column('recurrence_rule_id', sa.Uuid(), nullable=True))
    op.add_column('tasks', sa.Column('parent_task_id', sa.Uuid(), nullable=True))

    # Add check constraint for priority
    op.create_check_constraint('ck_task_priority_range', 'tasks', 'priority >= 1 AND priority <= 5')

    # Add foreign keys
    op.create_foreign_key(
        'fk_tasks_recurrence_rule_id',
        'tasks', 'recurrence_rules',
        ['recurrence_rule_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_tasks_parent_task_id',
        'tasks', 'tasks',
        ['parent_task_id'], ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for filtering and sorting
    op.create_index(op.f('ix_tasks_priority'), 'tasks', ['priority'], unique=False)
    op.create_index(op.f('ix_tasks_due'), 'tasks', ['due'], unique=False)
    op.create_index(op.f('ix_tasks_is_completed'), 'tasks', ['is_completed'], unique=False)

    # ==========================================================================
    # Create tags table
    # ==========================================================================
    op.create_table(
        'tags',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('color', sqlmodel.sql.sqltypes.AutoString(length=7), nullable=False, server_default='#6B7280'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_user_tag_name'),
    )
    op.create_index(op.f('ix_tags_user_id'), 'tags', ['user_id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=False)

    # ==========================================================================
    # Create task_tag junction table
    # ==========================================================================
    op.create_table(
        'task_tag',
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('tag_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id'),
    )
    op.create_index(op.f('ix_task_tag_task_id'), 'task_tag', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_tag_tag_id'), 'task_tag', ['tag_id'], unique=False)

    # ==========================================================================
    # Create reminders table
    # ==========================================================================
    op.create_table(
        'reminders',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('remind_at', sa.DateTime(), nullable=False),
        sa.Column('message', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_reminders_task_id'), 'reminders', ['task_id'], unique=False)
    op.create_index(op.f('ix_reminders_remind_at'), 'reminders', ['remind_at'], unique=False)
    op.create_index(op.f('ix_reminders_sent'), 'reminders', ['sent'], unique=False)

    # ==========================================================================
    # Create task_events table (audit log)
    # ==========================================================================
    op.create_table(
        'task_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('task_id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('event_data', sa.JSON(), nullable=True),
        sa.Column('published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_task_events_task_id'), 'task_events', ['task_id'], unique=False)
    op.create_index(op.f('ix_task_events_user_id'), 'task_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_task_events_event_type'), 'task_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_task_events_created_at'), 'task_events', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_events_published'), 'task_events', ['published'], unique=False)


def downgrade() -> None:
    """Remove Phase 5 advanced features tables and columns."""

    # Drop task_events table
    op.drop_index(op.f('ix_task_events_published'), table_name='task_events')
    op.drop_index(op.f('ix_task_events_created_at'), table_name='task_events')
    op.drop_index(op.f('ix_task_events_event_type'), table_name='task_events')
    op.drop_index(op.f('ix_task_events_user_id'), table_name='task_events')
    op.drop_index(op.f('ix_task_events_task_id'), table_name='task_events')
    op.drop_table('task_events')

    # Drop reminders table
    op.drop_index(op.f('ix_reminders_sent'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_remind_at'), table_name='reminders')
    op.drop_index(op.f('ix_reminders_task_id'), table_name='reminders')
    op.drop_table('reminders')

    # Drop task_tag junction table
    op.drop_index(op.f('ix_task_tag_tag_id'), table_name='task_tag')
    op.drop_index(op.f('ix_task_tag_task_id'), table_name='task_tag')
    op.drop_table('task_tag')

    # Drop tags table
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_index(op.f('ix_tags_user_id'), table_name='tags')
    op.drop_table('tags')

    # Remove columns and constraints from tasks table
    op.drop_index(op.f('ix_tasks_is_completed'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_due'), table_name='tasks')
    op.drop_index(op.f('ix_tasks_priority'), table_name='tasks')
    op.drop_constraint('fk_tasks_parent_task_id', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_recurrence_rule_id', 'tasks', type_='foreignkey')
    op.drop_constraint('ck_task_priority_range', 'tasks', type_='check')
    op.drop_column('tasks', 'parent_task_id')
    op.drop_column('tasks', 'recurrence_rule_id')
    op.drop_column('tasks', 'due')
    op.drop_column('tasks', 'priority')

    # Drop recurrence_rules table
    op.drop_index(op.f('ix_recurrence_rules_user_id'), table_name='recurrence_rules')
    op.drop_table('recurrence_rules')
