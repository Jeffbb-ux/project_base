"""Initial migration

Revision ID: b91e7807c296
Revises: 
Create Date: 2025-03-09 22:42:15.135177

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b91e7807c296'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=True, comment='系统根据证件信息生成的用户名，初始为空'),
    sa.Column('email', sa.String(length=255), nullable=False, comment='用户邮箱'),
    sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='加密后的密码'),
    sa.Column('registered_at', sa.DateTime(), nullable=True, comment='注册时间'),
    sa.Column('is_active', sa.Boolean(), nullable=True, comment='激活状态，注册后需通过邮箱验证激活'),
    sa.Column('activation_token', sa.String(length=64), nullable=True, comment='邮箱激活 token'),
    sa.Column('token_expires', sa.DateTime(), nullable=True, comment='激活 token 过期时间'),
    sa.Column('verification_status', sa.String(length=20), nullable=False, comment='用户审核状态：none, pending, approved, rejected'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_activation_token'), 'users', ['activation_token'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('ocr_results',
    sa.Column('id', sa.Integer(), nullable=False, comment='OCR 记录主键'),
    sa.Column('user_id', sa.Integer(), nullable=True, comment='上传该证件的用户ID'),
    sa.Column('doc_type', sa.String(length=50), nullable=False, comment="证件类型，例如 '身份证'、'驾照'、'护照'"),
    sa.Column('country', sa.String(length=50), nullable=False, comment='证件所属国家'),
    sa.Column('side', sa.String(length=10), nullable=True, comment="证件面向，例如 'front' 或 'back'"),
    sa.Column('document_number', sa.String(length=100), nullable=True, comment='证件号码'),
    sa.Column('name', sa.String(length=200), nullable=True, comment='证件上的姓名'),
    sa.Column('birth_date', sa.Date(), nullable=True, comment='出生日期'),
    sa.Column('expiry_date', sa.Date(), nullable=True, comment='证件有效期'),
    sa.Column('sex', sa.String(length=10), nullable=True, comment="性别，例如 'M' 或 'F'"),
    sa.Column('recognized_text', sa.Text(), nullable=True, comment='OCR 识别出的完整文本'),
    sa.Column('extracted_data', sa.JSON(), nullable=True, comment='提取的关键信息，存储为 JSON 格式'),
    sa.Column('confidence_score', sa.Float(), nullable=True, comment='OCR 识别置信度评分（0~1之间）'),
    sa.Column('status', sa.Enum('pending', 'success', 'failed', name='ocrstatus'), nullable=False, comment='OCR 处理状态'),
    sa.Column('error_message', sa.Text(), nullable=True, comment='OCR 识别失败时的错误描述'),
    sa.Column('review_required', sa.Boolean(), nullable=False, comment='是否需要人工审核'),
    sa.Column('upload_time', sa.DateTime(), nullable=False, comment='证件上传时间'),
    sa.Column('process_time', sa.DateTime(), nullable=True, comment='OCR 处理完成时间'),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='记录创建时间'),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='记录更新时间'),
    sa.Column('uploader_ip', sa.String(length=45), nullable=True, comment='上传者IP地址'),
    sa.Column('passport_image_path', sa.String(), nullable=True, comment='护照图片路径'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ocr_country', 'ocr_results', ['country'], unique=False)
    op.create_index('idx_ocr_doc_type', 'ocr_results', ['doc_type'], unique=False)
    op.create_index('idx_ocr_status', 'ocr_results', ['status'], unique=False)
    op.create_index(op.f('ix_ocr_results_id'), 'ocr_results', ['id'], unique=False)
    op.create_table('uploaded_passport',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False, comment='上传该证件的用户ID'),
    sa.Column('file_path', sa.String(), nullable=False, comment='护照图片存储路径'),
    sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='上传时间'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_uploaded_passport_id'), 'uploaded_passport', ['id'], unique=False)
    op.create_table('manual_reviews',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('ocr_result_id', sa.Integer(), nullable=False, comment='关联的OCR结果ID'),
    sa.Column('reviewer_id', sa.Integer(), nullable=True, comment='审核人ID'),
    sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='reviewstatus'), nullable=False, comment='审核状态'),
    sa.Column('remarks', sa.String(length=500), nullable=True, comment='审核备注信息'),
    sa.Column('created_at', sa.DateTime(), nullable=False, comment='审核创建时间'),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True, comment='审核完成时间'),
    sa.ForeignKeyConstraint(['ocr_result_id'], ['ocr_results.id'], ),
    sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_manual_reviews_id'), 'manual_reviews', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_manual_reviews_id'), table_name='manual_reviews')
    op.drop_table('manual_reviews')
    op.drop_index(op.f('ix_uploaded_passport_id'), table_name='uploaded_passport')
    op.drop_table('uploaded_passport')
    op.drop_index(op.f('ix_ocr_results_id'), table_name='ocr_results')
    op.drop_index('idx_ocr_status', table_name='ocr_results')
    op.drop_index('idx_ocr_doc_type', table_name='ocr_results')
    op.drop_index('idx_ocr_country', table_name='ocr_results')
    op.drop_table('ocr_results')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_activation_token'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
