import re
from typing import List

from src.lib.cdc.model import CDCSlot


def _extract_grid_html(response_text: str) -> str:
    """Extract the booking grid fragment that contains gvLatestav table."""
    table_match = re.search(
        r"(<table[^>]*id=\"ctl00_ContentPlaceHolder1_gvLatestav\"[\s\S]*?</table>)",
        response_text,
        flags=re.IGNORECASE,
    )
    return table_match.group(1) if table_match else ""


def _strip_html(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", text)
    return without_tags.replace("&nbsp;", " ").strip()


def _status_from_image_src(src: str) -> str:
    src_lower = src.lower()
    if "images1.gif" in src_lower:
        return "available"
    if "images2.gif" in src_lower:
        return "reserved"
    if "images3.gif" in src_lower:
        return "booked"
    return "unknown"


def extract_slots(response_text: str) -> List[CDCSlot]:
    """Parse slots from CDC ASP.NET AJAX response grid and return typed slot records."""
    grid_html = _extract_grid_html(response_text)
    if not grid_html:
        return []

    rows = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", grid_html, flags=re.IGNORECASE)
    if len(rows) < 2:
        return []

    header_cells = re.findall(r"<th[^>]*>([\s\S]*?)</th>", rows[0], flags=re.IGNORECASE)
    session_time_map: dict[int, str] = {}

    # First 2 header columns are date/day. Session columns start from index 2.
    for idx, cell in enumerate(header_cells[2:], start=1):
        br_match = re.search(
            r"(\d+)\s*<br\s*/?>\s*([0-9]{2}:[0-9]{2}\s*-\s*[0-9]{2}:[0-9]{2})",
            cell,
            flags=re.IGNORECASE,
        )
        if br_match:
            session_no = int(br_match.group(1))
            time_range = br_match.group(2).strip()
            session_time_map[session_no] = time_range
            continue

        plain = _strip_html(cell)
        split_match = re.match(r"(\d+)\s+(.+)", plain)
        if not split_match:
            continue
        session_no = int(split_match.group(1))
        time_range = split_match.group(2).strip()
        session_time_map[session_no] = time_range

    parsed_slots: List[CDCSlot] = []
    data_rows = rows[1:]

    for row_html in data_rows:
        cells = re.findall(r"<td[^>]*>([\s\S]*?)</td>", row_html, flags=re.IGNORECASE)
        if len(cells) < 3:
            continue

        session_date = _strip_html(cells[0])
        day = _strip_html(cells[1])
        if not session_date or not day:
            continue

        for col_index, cell_html in enumerate(cells[2:], start=1):
            img_match = re.search(r'src="([^"]+)"', cell_html, flags=re.IGNORECASE)
            if not img_match:
                continue
            image_src = img_match.group(1)
            image_name = image_src.rsplit("/", 1)[-1]
            status = _status_from_image_src(image_src)
            time_range = session_time_map.get(col_index, "")

            parsed_slots.append(
                CDCSlot(
                    session_date=session_date,
                    day=day,
                    session_number=col_index,
                    time_range=time_range,
                    status=status,
                    image_name=image_name,
                )
            )

    return parsed_slots
