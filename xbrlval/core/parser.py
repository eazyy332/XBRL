from __future__ import annotations

import io
from typing import Dict, List, Tuple
from urllib.parse import urljoin
from lxml import etree

from xbrlval.core.models import Instance, Context, Entity, Period, Unit, Fact
from xbrlval.util.fetch import fetch_to_bytes
from xbrlval.util.namespaces import NS


class XbrlInstanceParser:
    def __init__(self, base_uri: str):
        self.base_uri = base_uri

    def parse(self, source: str) -> Instance:
        xml_bytes, final_url = fetch_to_bytes(source)
        doc = etree.parse(io.BytesIO(xml_bytes))
        root = doc.getroot()

        schema_locations = [
            urljoin(final_url, el.get("{http://www.w3.org/1999/xlink}href"))
            for el in root.findall(".//link:schemaRef", namespaces=NS)
            if el.get("{http://www.w3.org/1999/xlink}href")
        ]
        linkbase_locations = [
            urljoin(final_url, el.get("{http://www.w3.org/1999/xlink}href"))
            for el in root.findall(".//link:linkbaseRef", namespaces=NS)
            if el.get("{http://www.w3.org/1999/xlink}href")
        ]

        contexts = self._parse_contexts(root)
        units = self._parse_units(root)
        facts = self._parse_facts(root)

        return Instance(
            base_uri=final_url,
            contexts=contexts,
            units=units,
            facts=facts,
            schema_locations=schema_locations,
            linkbase_locations=linkbase_locations,
        )

    def _parse_contexts(self, root) -> Dict[str, Context]:
        out: Dict[str, Context] = {}
        for ctx in root.findall("xbrli:context", namespaces=NS):
            ctx_id = ctx.get("id")
            if not ctx_id:
                continue
            entity_el = ctx.find("xbrli:entity", namespaces=NS)
            ident_el = entity_el.find("xbrli:identifier", namespaces=NS) if entity_el is not None else None
            ent = Entity(
                scheme=ident_el.get("scheme") if ident_el is not None else "",
                identifier=ident_el.text.strip() if ident_el is not None and ident_el.text else "",
            )
            period_el = ctx.find("xbrli:period", namespaces=NS)
            start_el = period_el.find("xbrli:startDate", namespaces=NS) if period_el is not None else None
            end_el = period_el.find("xbrli:endDate", namespaces=NS) if period_el is not None else None
            instant_el = period_el.find("xbrli:instant", namespaces=NS) if period_el is not None else None
            if instant_el is not None:
                period = Period(type="instant", start_date=None, end_date=None, instant=instant_el.text.strip() if instant_el.text else None)
            else:
                period = Period(
                    type="duration",
                    start_date=start_el.text.strip() if start_el is not None and start_el.text else None,
                    end_date=end_el.text.strip() if end_el is not None and end_el.text else None,
                    instant=None,
                )
            # Dimensions (very simplified, explicit only)
            dims: Dict[str, str] = {}
            for seg_dim in ctx.findall(".//xbrldi:explicitMember", namespaces=NS):
                dim_qname = seg_dim.get("dimension") or ""
                mem_qname = seg_dim.text.strip() if seg_dim.text else ""
                if dim_qname and mem_qname:
                    dims[dim_qname] = mem_qname
            out[ctx_id] = Context(id=ctx_id, entity=ent, period=period, dimensions=dims)
        return out

    def _parse_units(self, root) -> Dict[str, Unit]:
        out: Dict[str, Unit] = {}
        for unit in root.findall("xbrli:unit", namespaces=NS):
            unit_id = unit.get("id")
            if not unit_id:
                continue
            measures = [m.text.strip() for m in unit.findall("xbrli:measure", namespaces=NS) if m.text]
            num_measures = [m.text.strip() for m in unit.findall("xbrli:divide/xbrli:unitNumerator/xbrli:measure", namespaces=NS) if m.text]
            den_measures = [m.text.strip() for m in unit.findall("xbrli:divide/xbrli:unitDenominator/xbrli:measure", namespaces=NS) if m.text]
            out[unit_id] = Unit(id=unit_id, measures=measures, numerator_measures=num_measures or None, denominator_measures=den_measures or None)
        return out

    def _parse_facts(self, root) -> List[Fact]:
        facts: List[Fact] = []
        for el in root:
            if isinstance(el.tag, str) and not el.tag.startswith("{http://www.xbrl.org/2003/instance}"):
                # A fact element (simplified heuristic)
                context_ref = el.get("contextRef")
                unit_ref = el.get("unitRef")
                decimals = el.get("decimals")
                concept_qname = el.tag
                text = (el.text or "").strip() if el.text else None
                is_numeric = unit_ref is not None
                facts.append(Fact(concept=concept_qname, value=text, context_ref=context_ref, unit_ref=unit_ref, decimals=decimals, is_numeric=is_numeric))
        return facts