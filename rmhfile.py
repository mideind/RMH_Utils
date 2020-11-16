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


import xml.etree.cElementTree as ET
from collections import namedtuple
from pathlib import Path
import urllib.parse as urlparse


URI = "http://www.tei-c.org/ns/1.0"
TEI = "{" + URI + "}"
NS = {"tei": URI}
ET.register_namespace("", URI)

Sentence = namedtuple("Sentence", "index tokens")
Token = namedtuple("Token", "text, lemma, tag")


class RMHFile:
    """An xml file that is part of the RMH corpus"""

    def __init__(self, path):
        self.path = path if isinstance(path, Path) else Path(path)
        self._root = None
        self._header = None
        self._source_desc = None
        self._idno = None
        self._title = None 
        self._author = None
        self._date = None

    @classmethod
    def fromstring(cls, data):
        inst = cls("")
        inst._root = ET.fromstring(data)
        if inst.idno is None:
            return None
        inst.path = Path(inst.idno)
        inst.tsv_fname = inst.path.with_suffix(".tsv")
        inst.desc_fname = inst.path.with_suffix(".desc.xml")
        return inst

    @property
    def root(self):
        if self._root is not None:
            return self._root
        tree = ET.parse(self.path)
        self._root = tree.getroot()
        return self._root

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
            title_elem = header.find(".//tei:biblStruct/tei:analytic/tei:title/tei:title", NS)
            if title_elem is not None:
                return title_elem.text
        self._title = text
        return self._title

    @property
    def idno(self):
        if self._idno is not None:
            return self._idno
        idno_elem = self.root.find(".//tei:idno", NS)
        if idno_elem is None:
            return None
        self._idno = idno_elem.text
        return self._idno

    @property
    def paragraphs(self):
        for pg in self.root.iterfind(f".//tei:div1/tei:p", NS):
            yield pg

    @property
    def ref(self):
        if self.header is None:
            return None
        el = self.header.find(".//tei:biblScope/tei:ref", NS)
        if el is not None:
            return el.text
        return None

    @property
    def is_sports(self):
        if self.ref is None:
            return None
        res = urlparse.urlparse(self.ref)
        prefix = "/sport"
        infix = "/pepsi-deild/"
        items = self.header.iter(".//tei:keyWords/tei:list/tei:item")  # rmh2018/433/12/G-39-5740489
        found = any("Fótbolti" in item.text for item in items)
        return res.path.startswith(prefix) or infix in res.path or found

    def __fspath__(self):
        return str(self.path)

    def is_on_disk(self, directory):
        tsv_path = (Path(directory) / self.idno).with_suffix(".tsv")
        desc_path = (Path(directory) / self.idno).with_suffix(".desc.xml")
        if tsv_path.is_file() and desc_path.is_file():
            return True
        return False

    @property
    def sentences(self):
        idno = self.idno
        for pg in self.paragraphs:
            pg_idx = pg.attrib.get("n")
            for sentence in pg.iterfind("tei:s", NS):
                sent_idx = sentence.attrib.get("n")
                tokens = []
                for item in sentence:
                    token = Token(
                        item.text,
                        item.attrib.get("lemma", item.text),
                        item.attrib.get("type", item.text),
                    )
                    tokens.append(token)
                sent_id = f"{idno}.{pg_idx}.{sent_idx}"
                yield Sentence(sent_id, tokens)

    def indexed_sentence_text(self):
        for sentence in self.sentences:
            yield sentence.index, " ".join([token.text for token in sentence.tokens])
