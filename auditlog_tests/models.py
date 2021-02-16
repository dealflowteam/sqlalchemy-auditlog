import uuid

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from auditlog.registry import auditlog

Base = declarative_base()


class User(Base):
    """
    Simple user model
    """
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)


class SimpleModel(Base):
    """
    A simple model with no special things going on.
    """
    __tablename__ = 'simple_model'
    __mapper_args_ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'simple_model'
    }

    id = Column(Integer, primary_key=True)
    text = Column(String)
    boolean = Column(Boolean, default=False)
    integer = Column(Integer)
    datetime = Column(DateTime)

    related_models = relationship('RelatedModel', back_populates='related')

    def __str__(self):
        return f"Simple model: {self.text}"


class AltPrimaryKeyModel(Base):
    """
    A model with a non-standard primary key.
    """
    __tablename__ = 'alt_primary_key_model'

    key = Column(String, primary_key=True)
    text = Column(String)
    boolean = Column(Boolean, default=False)
    integer = Column(Integer)
    datetime = Column(DateTime)

    def __str__(self):
        return f"AltPrimaryKeyModel: {self.text}"


class UUIDPrimaryKeyModel(Base):
    """
   A model with a UUID primary key.
   """
    __tablename__ = 'uuid_primary_key_model'

    id = Column(UUID(as_uuid=True), default=uuid.uuid4, primary_key=True)
    text = Column(String)
    boolean = Column(Boolean, default=False)
    integer = Column(Integer)
    datetime = Column(DateTime)


class PolymorphicModel(SimpleModel):
    """
    A model that inherits from another model.
    """
    __mapper_args_ = {
        'polymorphic_identity': 'polymorphic_model'
    }


class RelatedModel(Base):
    """
    A model with a foreign key.
    """
    __tablename__ = 'related_model'

    id = Column(Integer, primary_key=True)
    related_id = Column(ForeignKey(SimpleModel.id))
    related = relationship(SimpleModel, back_populates='related_models')


simple_related = Table(
    'simple_related', Base.metadata,
    Column('related_model_id', Integer, ForeignKey('many_related_model.id')),
    Column('simple_model_id', Integer, ForeignKey(SimpleModel.id))
)


class ManyRelatedModel(Base):
    """
    A model with a many to many relation.
    """
    __tablename__ = 'many_related_model'

    id = Column(Integer, primary_key=True)
    text = Column(String)

    models = relationship('SimpleModel', secondary=simple_related)


@auditlog.register(include_fields=['label'])
class SimpleIncludeModel(Base):
    """
    A simple model used for register's include_fields kwarg
    """
    __tablename__ = 'simple_include_model'

    id = Column(Integer, primary_key=True)
    label = Column(String)
    text = Column(String)


class SimpleExcludeModel(Base):
    """
    A simple model used for register's exclude_fields kwarg
    """
    __tablename__ = 'simple_exclude_model'

    id = Column(Integer, primary_key=True)
    label = Column(String)
    text = Column(String)


auditlog.register(User)
auditlog.register(SimpleModel)
auditlog.register(AltPrimaryKeyModel)
auditlog.register(UUIDPrimaryKeyModel)
auditlog.register(PolymorphicModel)
auditlog.register(RelatedModel)
auditlog.register(ManyRelatedModel)
auditlog.register(SimpleExcludeModel, exclude_fields=['label'])
