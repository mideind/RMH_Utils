
from pathlib import Path

corpus_to_ordering = {
    "IGC-Adjud-22.10.TEI": "ordered",
    "IGC-Law-22.10.TEI": "ordered",
    "IGC-News1-22.10.TEI": "ordered",
    "IGC-News2-22.10.TEI": "ordered",
    "IGC-Parla-22.10.TEI": "ordered",
    "IGC-Wiki-22.10.TEI": "ordered",

    "IGC-Journals-22.10.TEI": "shuffled",
    "IGC-Social-22.10.TEI": "shuffled",

    "IGC-Books-22.10.TEI": "chunk-shuffled-500",
}


def lookup_ordering(path: Path):
    corpus = path.parts[0]

    if corpus in corpus_to_ordering:
        return corpus_to_ordering[corpus]
    else:
        return None



def adjud_igc2022(path: Path):
    level = path.parts[1]
    result = ["adjud"]
    if level == "District":
        result.append("heradsdomur")
    elif level == "Appeal":
        result.append("landsdomur")
    elif level == "Supreme":
        result.append("haestirettur")
    return result


journals_to_domains = {
    "ljo": "ljosmaedrabladid",
    "tu": "timarit-um-uppeldi-og-menntun",
    "lf": "logfraedingur",
    "bli": "bliki-timarit-um-fugla",
    "vt": "verktaekni-timarit-verkfraedinga-islands",
    "aif": "arbok-hins-islenska-fornleifafelgas",
    "tf": "timarit-felagsradgjafa",
    "im": "islenskt-mal-og-almenn-fraedi",
    "th": "timarit-hjukrunarfraedinga",
    "mf": "malfregnir-alyktanir-islenskrar-malnefndar",
    "tv": "timarit-um-vidskipti-og-efnahagsmal",
    "lb": "laeknabladid",
    "ski": "skirnir",
    "ith": "islenska-thjodfelgagid",
    "tlf": "timarit-logfradeinga",
    "ss": "stjornmal-og-stjornsysla",
    "hr": "hugras",
    "tlr": "timarit-logrettu-felags-laganema-vid-hr",
    "ri": "ritid-timarit-hugvisindastofnunar",
    "ne": "netla-veftimarit-um-uppeldi-og-menntun-fra-menntavisindasvidi-hi",
    "gr": "gripla",
    "rg": "ritrod-gudfraedistofnunar",
    "vv": "visindavefurinn",
}
# alternate version, not ascii-fied
"""
    "ljo": "Ljósmæðrablaðið",
    "tu": "Tímarit um uppeldi og menntun",
    "lf": "Lögfræðingur",
    "bli": "Bliki, tímarit um fugla",
    "vt": "Verktækni: Tímarit Verkfræðingafélags Íslands",
    "aif": "Árbók Hins íslenska fornleifafélags",
    "tf": "Tímarit félagsráðgjafa",
    "im": "Íslenskt mál og almenn málfræði",
    "th": "Tímarit hjúkrunarfræðinga",
    "mf": "Málfregnir - ályktanir Íslenskrar málnefndar",
    "tv": "Tímarit um viðskipti og efnahagsmál",
    "lb": "Læknablaðið",
    "ski": "Skírnir",
    "ith": "Íslenska þjóðfélagið",
    "tlf": "Tímarit lögfræðinga",
    "ss": "Stjórnmál og stjórnsýsla",
    "hr": "Hugrás",
    "tlr": "Tímarit Lögréttu: Félags laganema við HR",
    "ri": "Ritið: tímarit Hugvísindastofnunar",
    "ne": "Netla: Veftímarit um uppeldi og menntun frá menntavísindasviði HÍ",
    "gr": "Gripla",
    "rg": "Ritröð Guðfræðistofnunar",
    "vv": "Vísindavefurinn",
"""
def journals_igc2022(path: Path):
    journal_shorthand = path.parts[1]

    if journal_shorthand not in journals_to_domains:
        # Should not happen since we should know all the journals
        return ["journal"]

    return ["journal", journals_to_domains[journal_shorthand]]


def law_igc2022(path: Path):
    # Bills, Law or Proposals
    extra = path.parts[1].lower()
    if extra == "law":
        # Don't return ["law", "law"]
        return ["law"]
    return ["law", extra]


def news_igc2022(path: Path):
    # Lowercased name of publication
    extra = path.parts[1].lower()
    return ["news", extra]


def social_igc2022(path: Path):
    # Blog, Forum or Twitter
    social_type = path.parts[1].lower()

    if social_type == "twitter":
        return [social_type]

    # Name of forum or blog
    social_name = path.parts[2].lower()
    return [social_type, social_name]


# Map subcorpus to a function that returns the domains for that subcorpus
# Functions should take in the path of the file being processed
subcorpus_map = {
    "IGC-Adjud-22.10.TEI": adjud_igc2022,
    "IGC-Journals-22.10.TEI": journals_igc2022,
    "IGC-Law-22.10.TEI": law_igc2022,
    "IGC-News1-22.10.TEI": news_igc2022,
    "IGC-News2-22.10.TEI": news_igc2022,
    "IGC-Social-22.10.TEI": social_igc2022,

    "IGC-Parla-22.10.TEI": lambda _: ["parliament"],
    "IGC-Wiki-22.10.TEI": lambda _: ["wiki"],
    "IGC-Books-22.10.TEI": lambda _:["books"],
}
def lookup_domains(path: Path):
    return subcorpus_map[path.parts[0]](path)
