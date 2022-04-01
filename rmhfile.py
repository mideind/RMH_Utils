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
from typing import List
from xml.dom.minidom import Element

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

    @property
    def header(self):
        if self._header is not None:
            return self._header
        self._header = self.root.find(".//tei:teiHeader", NS)
        return self._header

    @property
    def author(self):
        if self._author is not None:
            return self._author
        header = self.header
        text = ""
        if header is not None:
            author_elem = header.find(".//tei:biblStruct/tei:analytic/tei:author", NS)
            if author_elem is not None and author_elem.text is not None:
                text = author_elem.text
        self._author = text
        return self._author

    @property
    def date(self):
        if self._date is not None:
            return self._date
        header = self.header
        text = ""
        if header is not None:
            date_elem = header.find(".//tei:biblStruct/tei:analytic/tei:date", NS)
            if date_elem is not None:
                text = date_elem.text
        self._date = text
        return self._date

    @property
    def title(self):
        if self._title is not None:
            return self._title
        header = self.header
        text = ""
        if header is not None:
            title_elem = header.find(".//tei:biblStruct/tei:analytic/tei:title", NS)
            if title_elem is not None:
                return title_elem.text
        self._title = text
        return self._title

    @property
    def idno(self):
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
            log.warning(f"No paragraphs found in file: {self.path}")
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
