"""Add conversation_id to ChatQuery

Revision ID: add_conversation_id
Revises: 
Create Date: 2025-10-10 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_conversation_id'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add the conversation_id column if it doesn't exist
    with op.batch_alter_table('chat_queries') as batch_op:
        # Check if the column already exists before adding
        try:
            batch_op.add_column(sa.Column('conversation_id', sa.String(64), nullable=True))
            batch_op.create_index(op.f('ix_chat_queries_conversation_id'), ['conversation_id'], unique=False)
        except Exception as e:
            print(f"Column might already exist: {e}")
        
        # Also add the other missing columns if they don't exist
        try:
            batch_op.add_column(sa.Column('confidence_score', sa.Float(), nullable=True))
            batch_op.add_column(sa.Column('response_time', sa.Float(), nullable=True))
            batch_op.add_column(sa.Column('rating', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('is_helpful', sa.Boolean(), nullable=True))
            batch_op.add_column(sa.Column('feedback_text', sa.Text(), nullable=True))
        except Exception as e:
            print(f"Some columns might already exist: {e}")


def downgrade():
    # Remove the added columns
    with op.batch_alter_table('chat_queries') as batch_op:
        batch_op.drop_index(op.f('ix_chat_queries_conversation_id'))
        batch_op.drop_column('conversation_id')
        batch_op.drop_column('confidence_score')
        batch_op.drop_column('response_time')
        batch_op.drop_column('rating')
        batch_op.drop_column('is_helpful')
        batch_op.drop_column('feedback_text')