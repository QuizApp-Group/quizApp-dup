"""Completely erase and drop all tables in the database. Useful for testing
or after changes in models.
"""

from sqlalchemy.engine import reflection
from sqlalchemy.schema import MetaData, Table, DropTable, DropConstraint, \
        ForeignKeyConstraint

from quizApp import db


def clear_db():
    """Reset the state of the database.
    """
    # https://bitbucket.org/zzzeek/sqlalchemy/wiki/UsageRecipes/DropEverything
    inspector = reflection.Inspector.from_engine(db.engine)
    metadata = MetaData()
    tables = []
    all_fks = []

    for table_name in inspector.get_table_names():
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if not fk['name']:
                continue
            fks.append(ForeignKeyConstraint((), (), name=fk['name']))
        table = Table(table_name, metadata, *fks)
        tables.append(table)
        all_fks.extend(fks)

    conn = db.engine.connect()
    trans = conn.begin()
    for fkc in all_fks:
        conn.execute(DropConstraint(fkc))

    for table in tables:
        conn.execute(DropTable(table))
    trans.commit()

    db.create_all()
