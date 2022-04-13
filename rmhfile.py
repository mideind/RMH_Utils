#!/usr/bin/env python3
"""
    Reynir: Natural language processing for Icelandic

     RMHFile

    Copyright (C) 2020 Miðeind ehf.

       This program is free software: you can redistribute it and/or modify
       it under the terms of the GNU General Public License as published by
       the Free Software Foundation, either version 3 of the License, or
       (at your option) any later version.
       This program is distributed in the hope that it will be useful,
       but WITHOUT ANY WARRANTY; without even the implied warranty of
       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
       GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see http://www.gnu.org/licenses/.

     Wrapper class for an xml resource file, as part of the RMH corpus.
"""

import logging
import xml.etree.cElementTree as ET
from collections import namedtuple
from pathlib import Path
from typing import List, Optional
from xml.etree.ElementTree import Element

log = logging.getLogger(__name__)

URI = "http://www.tei-c.org/ns/1.0"
TEI = "{" + URI + "}"
NS = {"tei": URI}
ET.register_namespace("", URI)

Sentence = namedtuple("Sentence", "index tokens")
Token = namedtuple("Token", "text, lemma, tag, id")


class RMHFile:
    """An xml file that is part of the RMH corpus"""

    def __init__(self, data: str, path: Path):
        self.path = path
        self.root = ET.fromstring(data)
        self._header = None
        self._idno = None
        self._title = None
        self._author = None
        self._date = None
        self._id = None

    @property
    def header(self) -> Element:
        """Return the header element"""
        if self._header is not None:
            return self._header
        header = self.root.find(".//tei:teiHeader", NS)
        if header is None:
            raise ValueError(f"No header found in file: {self.path}")
        self._header = header
        return self._header

    @property
    def author(self) -> Optional[str]:
        """Return the author element from the header"""
        if self._author is not None:
            return self._author
        author_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:author", NS)
        if author_elem is not None:
            self._author = author_elem.text
        return self._author

    @property
    def date(self) -> Optional[str]:
        """Return the date, if present, as string."""
        if self._date is not None:
            return self._date
        date_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:date", NS)
        if date_elem is not None:
            self._date = date_elem.text
        return self._date

    @property
    def is_adjud(self) -> bool:
        """Return True if this is an adjudication file"""
        return self.id.startswith("IGC-Adjud")

    @property
    def is_social(self) -> bool:
        """Return True if this is a social file"""
        return self.id.startswith("IGC-Social")

    @property
    def is_news(self) -> bool:
        """Return True if this is a news file"""
        return self.id.startswith("IGC-News")

    @property
    def title(self) -> str:
        """Return the title, if present, as string."""
        if self._title is not None:
            return self._title
        if self.is_social or self.is_news:
            title_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:title", NS)
        else:
            title_elem = self.header.find(".//tei:fileDesc/tei:titleStmt/tei:title[@type='sub']", NS)
        if title_elem is None or title_elem.text is None:
            raise ValueError(f"No title found in file: {self.path}")
        self._title = title_elem.text
        return self._title

    @property
    def id(self) -> str:
        """The id of the XML"""
        id_elem = self.root.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
        if id_elem is None:
            raise ValueError(f"No id found in file: {self.path}")
        self._id = id_elem
        return self._id

    @property
    def idno(self) -> Optional[str]:
        """Return the idno, if present, as string."""
        if self._idno is not None:
            return self._idno
        idno_elem = self.root.find(".//tei:idno", NS)  # idno is in IGC-Adjud
        if idno_elem is None:
            idno_elem = self.root.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
        if idno_elem is None:
            log.warning("No idno element found in %s", self.path)
        self._idno = idno_elem
        return self._idno

    def ref(self):
        """Return the reference for this file"""
        if self.header is None:
            return None
        el = self.header.find(".//tei:biblScope/tei:ref", NS)
        if el is not None:
            return el.text
        return None

    def _paragraphs(self) -> List[Element]:
        pgs = list(self.root.iterfind(f".//tei:div/tei:p", NS))
        if len(pgs) == 0:
            pgs = list(self.root.iterfind(f".//tei:u/tei:seg", NS))
        if len(pgs) == 0:
            # normally tei:div/tei:p, but tei:u/tei:seg for IGC-Parla
            raise ValueError(f"No paragraphs found in file: {self.path}")
        return pgs  # type: ignore

    def paragraphs(self) -> List[str]:
        """for now just collecting paragraphs from the TEI untokenized format"""
        return [pg.text for pg in self._paragraphs() if pg.text is not None]

    def sentences(self):
        idno = self.idno
        for pg in self._paragraphs():
            pg_idx = pg.attrib.get("n")
            for sentence in pg.iterfind("tei:s", NS):
                sent_idx = sentence.attrib.get("n")
                tokens = []
                for item in sentence:
                    token = Token(
                        item.text,
                        item.attrib.get("lemma", item.text),
                        item.attrib.get("pos", item.text),
                        item.attrib.get("xml:id", item.text),
                    )
                    tokens.append(token)
                sent_id = f"{idno}.{pg_idx}.{sent_idx}"
                yield Sentence(sent_id, tokens)
