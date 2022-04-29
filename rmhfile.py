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
from typing import Iterable, List, Optional
from xml.etree.ElementTree import Element

log = logging.getLogger(__name__)

URI = "http://www.tei-c.org/ns/1.0"
TEI = "{" + URI + "}"
NS = {"tei": URI}
ET.register_namespace("", URI)

RMHSentence = namedtuple("RMHSentence", "index tokens")
RMHToken = namedtuple("RMHToken", "text lemma tag id")


class RMHFile:
    """An xml file that is part of the RMH corpus"""

    def __init__(self, data: str, path: Path):
        self.path = path
        self.root = ET.fromstring(data)

    @property
    def header(self) -> Element:
        """Return the header element"""
        header = self.root.find(".//tei:teiHeader", NS)
        if header is None:
            raise ValueError(f"No header found in file: {self.path}")
        return header

    @property
    def author(self) -> Optional[str]:
        """Return the author text, if present."""
        author_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:author", NS)
        if author_elem is not None:
            return author_elem.text
        return None

    @property
    def date(self) -> Optional[str]:
        """Return the date string, if present."""
        date_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:date", NS)
        if date_elem is not None:
            return date_elem.text
        return None

    @property
    def title(self) -> str:
        """Return the title string, if present."""
        if self.is_social or self.is_news:
            title_elem = self.header.find(".//tei:biblStruct/tei:analytic/tei:title", NS)
        else:
            title_elem = self.header.find(".//tei:fileDesc/tei:titleStmt/tei:title[@type='sub']", NS)
        if title_elem is None or title_elem.text is None:
            raise ValueError(f"No title found in file: {self.path}")
        return title_elem.text

    @property
    def id(self) -> str:
        """The id of the XML"""
        id_elem = self.root.attrib.get("{http://www.w3.org/XML/1998/namespace}id")
        if id_elem is None:
            raise ValueError(f"No id found in file: {self.path}")
        return id_elem

    @property
    def idno(self) -> Optional[str]:
        """Return the idno as string, if present."""
        idno_elem = self.root.find(".//tei:idno", NS)  # idno is in IGC-Adjud
        if idno_elem is not None:
            return idno_elem.text
        return self.root.attrib.get("{http://www.w3.org/XML/1998/namespace}id")

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

    def ref(self):
        """Return the reference for this file"""
        el = self.header.find(".//tei:biblScope/tei:ref", NS)
        if el is not None:
            return el.text
        return None

    def _paragraphs(self) -> List[Element]:
        pgs = list(self.root.iterfind(".//tei:div/tei:p", NS))
        if len(pgs) == 0:
            pgs = list(self.root.iterfind(".//tei:u/tei:seg", NS))
        if len(pgs) == 0:
            # normally tei:div/tei:p, but tei:u/tei:seg for IGC-Parla
            raise ValueError(f"No paragraphs found in file: {self.path}")
        return pgs  # type: ignore

    def paragraphs(self) -> List[str]:
        """for now just collecting paragraphs from the TEI untokenized format"""
        return [pg.text for pg in self._paragraphs() if pg.text is not None]

    def sentences(self) -> Iterable[RMHSentence]:
        """Return all the sentences in this file."""
        idno = self.idno
        for pg in self._paragraphs():
            pg_idx = pg.attrib.get("n")
            for sentence in pg.iterfind("tei:s", NS):
                sent_idx = sentence.attrib.get("n")
                tokens = []
                for item in sentence:
                    token = RMHToken(
                        item.text,
                        item.attrib.get("lemma", item.text),
                        item.attrib.get("pos", item.text),
                        item.attrib.get("xml:id", item.text),
                    )
                    tokens.append(token)
                sent_id = f"{idno}.{pg_idx}.{sent_idx}"
                yield RMHSentence(sent_id, tokens)
