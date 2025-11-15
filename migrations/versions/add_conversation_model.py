"""Add Conversation model and update ChatQuery

Revision ID: add_conversation_model
Revises: 
Create Date: 2025-10-10 19:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_conversation_model'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table if it doesn't exist
    try:
        op.create_table(
            'conversations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('session_id', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_conversations_session_id'), 'conversations', ['session_id'], unique=True)
        op.create_index(op.f('ix_conversations_user_id'), 'conversations', ['user_id'], unique=False)
    except:
        print("Conversations table might already exist")
    
    # Add columns to chat_queries table if they don't exist
    with op.batch_alter_table('chat_queries') as batch_op:
        # Add conversation_id column
        try:
            batch_op.add_column(sa.Column('conversation_id', sa.String(length=64), nullable=True))
            batch_op.create_index(op.f('ix_chat_queries_conversation_id'), ['conversation_id'], unique=False)
        except:
            print("conversation_id column might already exist")
            
        # Add analytics columns
        try:
            batch_op.add_column(sa.Column('confidence_score', sa.Float(), nullable=True))
        except:
            print("confidence_score column might already exist")
            
        try:
            batch_op.add_column(sa.Column('response_time', sa.Float(), nullable=True))
        except:
            print("response_time column might already exist")
            
        try:
            batch_op.add_column(sa.Column('rating', sa.Integer(), nullable=True))
        except:
            print("rating column might already exist")
            
        try:
            batch_op.add_column(sa.Column('is_helpful', sa.Boolean(), nullable=True))
        except:
            print("is_helpful column might already exist")
            
        try:
            batch_op.add_column(sa.Column('feedback_text', sa.Text(), nullable=True))
        except:
            print("feedback_text column might already exist")


def downgrade():
    # This is intentionally empty as we don't want to drop anything in case of rollback
    pass