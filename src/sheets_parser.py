import re
import csv
import tempfile
from googleapiclient.discovery import build
import logging
import json


def get_direct_drive_link(url: str) -> str:
    """
    Convert a standard Google Drive sharing URL to a direct link.
    For example, converts:
      https://drive.google.com/file/d/14Styx777G3sWUH6iVYiHl87Lm4QIIhuv/view?usp=share_link
    to:
      https://drive.google.com/uc?export=view&id=14Styx777G3sWUH6iVYiHl87Lm4QIIhuv
    """
    match = re.search(r"/d/([^/]+)", url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=view&id={file_id}"
    return url


def debug_dump_sheet(sheet_url: str, api_key: str):
    """
    Fetches the full grid data (includeGridData=True) for the given sheet URL
    and prints out all properties for each cell in a readable JSON format.
    """
    # Extract spreadsheet ID from URL.
    import re

    match = re.search(r"/d/([^/]+)", sheet_url)
    if not match:
        raise ValueError("Invalid Google Sheets URL format.")
    spreadsheet_id = match.group(1)

    # Assume the first sheet; adjust the range if needed.
    sheet_range = "Sheet1"

    # Build the service.
    service = build("sheets", "v4", developerKey=api_key)

    result = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            ranges=sheet_range,
            includeGridData=True,
        )
        .execute()
    )

    sheets = result.get("sheets", [])
    if not sheets:
        print("No sheets found.")
        return

    grid_data = sheets[0].get("data", [])
    if not grid_data:
        print("No grid data found.")
        return

    rowData = grid_data[0].get("rowData", [])
    if not rowData:
        print("No row data found.")
        return

    # Dump cell properties for each row.
    for i, row in enumerate(rowData):
        values = row.get("values", [])
        print(f"--- Row {i} ---")
        for j, cell in enumerate(values):
            print(f"Cell {j}:")
            print(json.dumps(cell, indent=2))
            print()  # blank line for readability


def google_sheet_to_csv(sheet_url: str, api_key: str) -> str:
    """
    Uses the Google Sheets API with includeGridData to fetch the full cell data from a public sheet.
    For the "Image" column, if a cell contains a hyperlink (the actual image URL), it is used;
    otherwise, the formatted value is used. If the URL appears to be a Google Drive sharing URL,
    it's converted to a direct link.

    Returns the path to a temporary CSV file with the sheet data.
    """
    # Extract the spreadsheet ID from the URL.
    import re

    match = re.search(r"/d/([^/]+)", sheet_url)
    if not match:
        raise ValueError("Invalid Google Sheets URL format.")
    spreadsheet_id = match.group(1)

    # Assume the first sheet. You can adjust this if needed.
    sheet_range = "Sheet1"

    # Build the Sheets API service.
    service = build("sheets", "v4", developerKey=api_key)

    # Get the full sheet with grid data.
    result = (
        service.spreadsheets()
        .get(
            spreadsheetId=spreadsheet_id,
            ranges=sheet_range,
            includeGridData=True,
        )
        .execute()
    )

    sheets = result.get("sheets", [])
    if not sheets:
        raise ValueError("No sheets found in the spreadsheet.")

    # Use the first sheet's first data block.
    grid_data = sheets[0].get("data", [])
    if not grid_data:
        raise ValueError("No grid data found in the sheet.")

    rowData = grid_data[0].get("rowData", [])
    if not rowData:
        raise ValueError("No row data found in the sheet.")

    # Build header from first row.
    header = []
    first_row = rowData[0].get("values", [])
    for cell in first_row:
        header.append(cell.get("formattedValue", "").strip())

    # Identify the index for the "Image" column.
    image_col_index = None
    for idx, col in enumerate(header):
        if col.lower() == "image":
            image_col_index = idx
            break

    # Process subsequent rows.
    processed_rows = [header]
    for i, row in enumerate(rowData[1:], start=1):
        values = row.get("values", [])
        row_values = []
        for j in range(len(header)):
            cell = values[j] if j < len(values) else {}
            # If the cell has a hyperlink, use that; otherwise, fallback to formattedValue.
            cell_value = (
                cell.get("hyperlink") or cell.get("formattedValue", "").strip()
            )
            # For the Image column, if it looks like a Drive sharing link, convert it.
            if (
                image_col_index is not None
                and j == image_col_index
                and cell_value
            ):
                if (
                    "drive.google.com/file/d/" in cell_value
                    and "/view" in cell_value
                ):
                    cell_value = get_direct_drive_link(cell_value)
            row_values.append(cell_value)
        processed_rows.append(row_values)

    # Write the processed data to a temporary CSV file.
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    with open(tmp_file.name, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(processed_rows)
    return tmp_file.name
