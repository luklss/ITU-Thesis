from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from PIL import Image
import os
import configparser
config = configparser.ConfigParser()
self_path = os.path.dirname(os.path.abspath(__file__))
config.read(os.path.join(self_path, "alembic.ini"))
image_dir  = config['alembic']['image_dir']

Base = declarative_base()
# THEN WHEN CREATING:
# Base.metadata.create_all(engine)

TaggedImages = Table("TaggedImages",
    Base.metadata,
    Column("imageID", String(100), ForeignKey("Images.imageHASH")),
    Column("tagID", Integer, ForeignKey('Tags.tagID'))
)

class Images(Base):

    __tablename__ = "Images"

    imageHASH   = Column(String(100), primary_key=True)
    name        = Column(String(100), nullable=False)
    source      = Column(String(100), nullable=False)
    filetype    = Column(String(100), nullable=False)
    timestamp   = Column(DateTime, nullable=False)
    url         = Column(String(100), nullable=True)
    origin      = Column(String(100), nullable=False)
    position    = Column(Integer, nullable=True)

    # relationship fields:
    labels      = relationship("Labels")
    tags        = relationship("Tags",
                    secondary=TaggedImages,
                    back_populates="images",
                )

    def get_image(self, image_dir_root=None):
        """ return a PIL image representation of this image """
        image_dir_root = image_dir_root or image_dir
        return Image.open(path.join(image_dir_root, self.name))

    def show(self, image_dir_root=None):
        """ A method for showing the image represented by an instantiation of this model
        """
        self.get_image(image_dir_root=image_dir_root).show()

    def __repr__(self):
        return "<Image imageHASH='%s', name='%s'>" % (self.imageHASH, self.name)



class Tags(Base):

    __tablename__   = "Tags"

    tagID   = Column(Integer, primary_key=True)
    tagName = Column(String(100), nullable=False)

    # relationship fields:
    images  = relationship("Images",
                secondary=TaggedImages,
                back_populates="tags",
            )

    def __repr__(self):
        return "<Tags tagID=%s, tagName='%s'" % (
                self.tagID, self.tagName)


class Comparisons(Base):
    """
    A model class for comparison based votes
    """

    __tablename__ = "Comparisons"

    comparisonID  = Column(Integer, primary_key=True)
    imageID_1     = Column(String(100), ForeignKey('Images.imageHASH'))
    imageID_2     = Column(String(100), ForeignKey('Images.imageHASH'))
    win1          = Column(Integer, nullable=False)
    win2          = Column(Integer, nullable=False)
    tie           = Column(Integer, nullable=False)
    source        = Column(String(100))
    timestamp     = Column(DateTime, nullable=False)

    __table_args__ = (
        UniqueConstraint('imageID_1', 'imageID_2', name="pair"),
        CheckConstraint('imageID_1 <> imageID_2', name='check-is-different'),
        CheckConstraint('max(imageID_1, imageID_2) = imageID_2', name='ordered-pair'),
    )

    def __repr__(self):
        return ("<Votes comparisonID=%s, imageID_1='%s', imageID_2='%s', win1=%s, "
               "win2=%s, tie=%s>") % (
                    self.comparisonID,
                    self.imageID_1,
                    self.imageID_2,
                    self.win1,
                    self.win2,
                    self.tie
                )


class ProtestNonProtestVotes(Base):
    """
    A model class for labels on whether image is from a protest or not.
    """

    __tablename__ = "ProtestNonProtestVotes"

    protestVoteID = Column(Integer, primary_key=True)
    imageID       = Column(String(100), ForeignKey('Images.imageHASH'))
    annotator     = Column(String(100), nullable=True)
    is_protest    = Column(Boolean, nullable=False)
    timestamp     = Column(DateTime, nullable=False)

    def __repr__(self):
        return ("<ProtestNonProtestVotes protestVoteID=%s, imageID='%s', "
               "is_protest=%s, timestamp='%s'>") % (
                self.protestVoteID, self.imageID, self.is_protest, self.timestamp)


class Labels(Base):
    """
    A class for labeling image as violent or not - where the label itself
    is a floating point between 0 and 1
    """

    __tablename__ = "Labels"

    labelID     = Column(Integer, primary_key=True)
    imageID     = Column(String(100), ForeignKey('Images.imageHASH'))
    source      = Column(String(100))
    timestamp   = Column(DateTime, nullable=False)
    label       = Column(Float, nullable=False)

    def __repr__(self):
        return "<Labels labelID=%s, imageID='%s', label='%s'>" % (
                self.labelID, self.imageID, self.label)
