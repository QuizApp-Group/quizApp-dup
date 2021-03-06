"""empty message

Revision ID: 20fbb13ea446
Revises: 16d60457aa72
Create Date: 2016-09-15 13:09:43.802148

"""

# revision identifiers, used by Alembic.
revision = '20fbb13ea446'
down_revision = '16d60457aa72'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('activity', 'tolerance')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('activity', sa.Column('tolerance', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    ### end Alembic commands ###
