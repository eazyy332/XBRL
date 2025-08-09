from __future__ import annotations

import io
from collections import defaultdict
from typing import Dict, List, Tuple
from urllib.parse import urljoin
from lxml import etree

from xbrlval.core.models import Instance
from xbrlval.util.fetch import fetch_to_bytes
from xbrlval.util.namespaces import NS


class CalculationLinkbase:
    def __init__(self):
        # role -> parentConcept -> List[(childConcept, weight)]
        self.trees_by_role: Dict[str, Dict[str, List[Tuple[str, float]]]] = defaultdict(lambda: defaultdict(list))

    def load_from_instance(self, instance: Instance) -> None:
        # Load linkbases directly referenced in the instance
        for href in instance.linkbase_locations:
            xml_bytes, final_url = fetch_to_bytes(href)
            self._parse_linkbase(xml_bytes)

        # Attempt to load linkbases referenced from schemas (best-effort; not full DTS)
        for schema_href in instance.schema_locations:
            try:
                xml_bytes, final_url = fetch_to_bytes(schema_href)
                doc = etree.parse(io.BytesIO(xml_bytes))
                root = doc.getroot()
                for lbref in root.findall(".//link:linkbaseRef", namespaces=NS):
                    href = lbref.get("{http://www.w3.org/1999/xlink}href")
                    if not href:
                        continue
                    full = urljoin(final_url, href)
                    lb_bytes, _ = fetch_to_bytes(full)
                    self._parse_linkbase(lb_bytes)
            except Exception:
                continue

    def _parse_linkbase(self, xml_bytes: bytes) -> None:
        doc = etree.parse(io.BytesIO(xml_bytes))
        root = doc.getroot()
        for calcLink in root.findall("link:calculationLink", namespaces=NS):
            role = calcLink.get("{http://www.w3.org/1999/xlink}role") or "Default"
            # Build locator map
            loc_to_concept: Dict[str, str] = {}
            for loc in calcLink.findall("link:loc", namespaces=NS):
                loc_label = loc.get("{http://www.w3.org/1999/xlink}label")
                href = loc.get("{http://www.w3.org/1999/xlink}href")
                if not loc_label or not href:
                    continue
                # href like file.xsd#concept
                if "#" in href:
                    concept = href.split("#", 1)[1]
                else:
                    concept = href
                loc_to_concept[loc_label] = concept
            for arc in calcLink.findall("link:calculationArc", namespaces=NS):
                frm = arc.get("{http://www.w3.org/1999/xlink}from")
                to = arc.get("{http://www.w3.org/1999/xlink}to")
                weight = arc.get("weight")
                if not frm or not to or weight is None:
                    continue
                try:
                    w = float(weight)
                except Exception:
                    continue
                parent_concept = loc_to_concept.get(frm)
                child_concept = loc_to_concept.get(to)
                if not parent_concept or not child_concept:
                    continue
                self.trees_by_role[role][parent_concept].append((child_concept, w))