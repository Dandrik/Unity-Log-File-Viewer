"""Elekta MLC Status and Fault Code Definitions.

Comprehensive lookup table mapping Elekta MLC controller status, interlock,
and error codes to their official descriptions.
"""

from typing import Any, Dict, Optional

ELEKTA_MLC_CODES: Dict[int, str] = {
    0: "MLC OK",
    1: "MLC OK",
    7000: "Prescription Not OK",
    7001: "Not Calibrated",
    7002: "Movement",
    7003: "Single Closed Leaf",
    7004: "Null Shape Code",
    7005: "Illegal Shape Code",
    7006: "Start Stop Not Valid",
    7007: "Leaf Proximity",
    7008: "Unexpected Open Leaf",
    7009: "Leaf Overlap",
    7010: "Wedge Field Size",
    7011: "Energy Error",
    7012: "Missing ID",
    7013: "Illegal Segment ID",
    7014: "Illegal Step ID",
    7015: "Incorrect Sequence ID",
    7016: "Applicator Error",
    7017: "Applicator Size Error",
    7018: "Autotracking not set",
    7019: "Wedge Modality",
    7020: "Illegal X Coordinate",
    7021: "Illegal Y Coordinate",
    7022: "Consistency Check",
    7023: "Diaphragm Proximity",
    7030: "Head Type Unknown",
    7031: "Head Type Incorrect",
    7040: "Lost Reflector Rate",
    7050: "Illumination Error 01",
    7051: "Illumination Error 02",
    7052: "Illumination Error 03",
    7053: "Illumination Error 04",
    7060: "Unexpected Exception",
    7061: "Invalid Item",
    7062: "Invalid Part",
    7063: "Invalid Value",
    7070: "PRF Control Error",
    7071: "No Dose Rate",
    7072: "No PRF Code",
    7073: "PRF Interlock",
    7074: "HT Interlock",
    7100: "Reference Reflector",
    7102: "Reference Reflector X Not Foun",
    7103: "Reference Reflector Y Not Foun",
    7105: "Reference Reflector X Position",
    7106: "Reference Reflector Y Position",
    7200: "Leaf Confirmation",
    7201: "Start Confirm Error",
    7202: "Confirm Error",
    7203: "Confirm S/W Error",
    7204: "Video Line Spacing Error",
    7205: "Parking Leaves",
    7206: "Parking Error",
    7207: "Parking S/W Error",
    7300: "Leaves not Ready Y2",
    7310: "Leaves not Ready Y1",
    7323: "Too Many Reflectors",
    7324: "Lost Leaf Refl",
    7411: "Leaf Limit Switch",
    7413: "Readout 10V or 0V Ref",
    7414: "Signal Supplies",
    7430: "DLG Position Y2",
    7440: "DLG Position Y1",
    7450: "Diaphragm Position X1",
    7451: "Ten Turn Pot X1",
    7452: "Check Pot X1",
    7453: "Fine Pot Offset X1",
    7454: "Uncorrelated Pot X1",
    7460: "Diaphragm Position X2",
    7461: "Ten Turn Pot X2",
    7462: "Check Pot X2",
    7463: "Fine Pot Offset X2",
    7464: "Uncorrelated Pot X2",
    7470: "Diaphragm Position Y2",
    7471: "Ten Turn Pot Y2",
    7472: "Check Pot Y2",
    7473: "Fine Pot Offset Y2",
    7474: "Uncorrelated Pot Y2",
    7480: "Diaphragm Position Y1",
    7481: "Ten Turn Pot Y1",
    7482: "Check Pot Y1",
    7483: "Fine Pot Offset Y1",
    7484: "Uncorrelated Pot Y1",
    7501: "Y2 Leaf 01 Refl Size Error",
    7502: "Y2 Leaf 02 Refl Size Error",
    7503: "Y2 Leaf 03 Refl Size Error",
    7504: "Y2 Leaf 04 Refl Size Error",
    7505: "Y2 Leaf 05 Refl Size Error",
    7506: "Y2 Leaf 06 Refl Size Error",
    7507: "Y2 Leaf 07 Refl Size Error",
    7508: "Y2 Leaf 08 Refl Size Error",
    7509: "Y2 Leaf 09 Refl Size Error",
    7510: "Y2 Leaf 10 Refl Size Error",
    7511: "Y2 Leaf 11 Refl Size Error",
    7512: "Y2 Leaf 12 Refl Size Error",
    7513: "Y2 Leaf 13 Refl Size Error",
    7514: "Y2 Leaf 14 Refl Size Error",
    7515: "Y2 Leaf 15 Refl Size Error",
    7516: "Y2 Leaf 16 Refl Size Error",
    7517: "Y2 Leaf 17 Refl Size Error",
    7518: "Y2 Leaf 18 Refl Size Error",
    7519: "Y2 Leaf 19 Refl Size Error",
    7520: "Y2 Leaf 20 Refl Size Error",
    7521: "Y2 Leaf 21 Refl Size Error",
    7522: "Y2 Leaf 22 Refl Size Error",
    7523: "Y2 Leaf 23 Refl Size Error",
    7524: "Y2 Leaf 24 Refl Size Error",
    7525: "Y2 Leaf 25 Refl Size Error",
    7526: "Y2 Leaf 26 Refl Size Error",
    7527: "Y2 Leaf 27 Refl Size Error",
    7528: "Y2 Leaf 28 Refl Size Error",
    7529: "Y2 Leaf 29 Refl Size Error",
    7530: "Y2 Leaf 30 Refl Size Error",
    7531: "Y2 Leaf 31 Refl Size Error",
    7532: "Y2 Leaf 32 Refl Size Error",
    7533: "Y2 Leaf 33 Refl Size Error",
    7534: "Y2 Leaf 34 Refl Size Error",
    7535: "Y2 Leaf 35 Refl Size Error",
    7536: "Y2 Leaf 36 Refl Size Error",
    7537: "Y2 Leaf 37 Refl Size Error",
    7538: "Y2 Leaf 38 Refl Size Error",
    7539: "Y2 Leaf 39 Refl Size Error",
    7540: "Y2 Leaf 40 Refl Size Error",
    7541: "Y1 Leaf 01 Refl Size Error",
    7542: "Y1 Leaf 02 Refl Size Error",
    7543: "Y1 Leaf 03 Refl Size Error",
    7544: "Y1 Leaf 04 Refl Size Error",
    7545: "Y1 Leaf 05 Refl Size Error",
    7546: "Y1 Leaf 06 Refl Size Error",
    7547: "Y1 Leaf 07 Refl Size Error",
    7548: "Y1 Leaf 08 Refl Size Error",
    7549: "Y1 Leaf 09 Refl Size Error",
    7550: "Y1 Leaf 10 Refl Size Error",
    7551: "Y1 Leaf 11 Refl Size Error",
    7552: "Y1 Leaf 12 Refl Size Error",
    7553: "Y1 Leaf 13 Refl Size Error",
    7554: "Y1 Leaf 14 Refl Size Error",
    7555: "Y1 Leaf 15 Refl Size Error",
    7556: "Y1 Leaf 16 Refl Size Error",
    7557: "Y1 Leaf 17 Refl Size Error",
    7558: "Y1 Leaf 18 Refl Size Error",
    7559: "Y1 Leaf 19 Refl Size Error",
    7560: "Y1 Leaf 20 Refl Size Error",
    7561: "Y1 Leaf 21 Refl Size Error",
    7562: "Y1 Leaf 22 Refl Size Error",
    7563: "Y1 Leaf 23 Refl Size Error",
    7564: "Y1 Leaf 24 Refl Size Error",
    7565: "Y1 Leaf 25 Refl Size Error",
    7566: "Y1 Leaf 26 Refl Size Error",
    7567: "Y1 Leaf 27 Refl Size Error",
    7568: "Y1 Leaf 28 Refl Size Error",
    7569: "Y1 Leaf 29 Refl Size Error",
    7570: "Y1 Leaf 30 Refl Size Error",
    7571: "Y1 Leaf 31 Refl Size Error",
    7572: "Y1 Leaf 32 Refl Size Error",
    7573: "Y1 Leaf 33 Refl Size Error",
    7574: "Y1 Leaf 34 Refl Size Error",
    7575: "Y1 Leaf 35 Refl Size Error",
    7576: "Y1 Leaf 36 Refl Size Error",
    7577: "Y1 Leaf 37 Refl Size Error",
    7578: "Y1 Leaf 38 Refl Size Error",
    7579: "Y1 Leaf 39 Refl Size Error",
    7580: "Y1 Leaf 40 Refl Size Error",
    7610: "CAN MLC State Machine",
    7611: "CAN MLC Watchdog",
    7612: "CAN MLC CRC",
    7613: "CAN H/W Reset",
    7614: "CAN MLC S/W Reset",
    7615: "All Voltage Rails",
    7616: "All Serial Comms",
    7617: "All Watchdogs",
    7618: "All Fans",
    7619: "All Temperatures",
    7620: "All Interlocks",
    7621: "Router Voltage Rails",
    7622: "Router CAN Watchdog",
    7623: "Router Watchdog",
    7624: "Router Fan",
    7625: "Router CAN Rx",
    7626: "Router CAN FIFO",
    7627: "Router CAN Control",
    7628: "Router CAN Page",
    7629: "LED Voltage Rails",
    7630: "LED Serial Comms Link",
    7632: "LED Fan",
    7633: "LED Temperature",
    7634: "Router Sequencer",
    7635: "Router SPI",
    7636: "Accessory Voltage Rails",
    7637: "Accessory Serial Comms Link",
    7638: "Sync Detect Remote",
    7639: "Video Detect Remote",
    7640: "DLG Voltage Rails",
    7641: "DLG Serial Comms Link",
    7642: "DLG Watchdog",
    7643: "DLG Sequencer",
    7644: "DLG SPI",
    7645: "Diaphragm Voltage Rails",
    7646: "Diaphragm Serial Comms",
    7647: "Diaphragm Watchdog",
    7648: "LMDB Y11 Voltage Rails",
    7649: "LMDB Y11 Serial Comms",
    7650: "LMDB Y11 Watchdog",
    7651: "LMDB Y11 Fan",
    7652: "LMDB Y11 Temperature",
    7653: "LMDB Sequencer",
    7654: "LMDB SPI",
    7655: "LMDB Y12 Voltage Rails",
    7656: "LMDB Y12 Serial Comms",
    7657: "LMDB Y12 Watchdog",
    7658: "LMDB Y12 Fan",
    7659: "LMDB Y12 Temperature",
    7660: "LMDB Y21 Voltage Rails",
    7661: "LMDB Y21 Serial Comms",
    7662: "LMDB Y21 Watchdog",
    7663: "LMDB Y21 Fan",
    7664: "LMDB Y21 Temperature",
    7665: "LMDB Y22 Voltage Rails",
    7666: "LMDB Y22 Serial Comms",
    7667: "LMDB Y22 Watchdog",
    7668: "LMDB Y22 Fan",
    7669: "LMDB Y22 Temperature",
    7670: "Wedge Voltage Rails",
    7671: "Wedge Serial Comms",
    7672: "DLG 24V Enable",
    7673: "Diaphragm 24V Enable",
    7674: "CCU Sync Detect",
    7701: "Head Control Demand",
    7703: "Head Controls",
    7710: "MLC CAN Link",
    7711: "MLC CAN Link 01",
    7712: "MLC CAN Link 02",
    7713: "MLC CAN Link 03",
    7714: "MLC CAN Link 04",
    7715: "MLC CAN Link 05",
    7716: "MLC CAN Link 06",
    7717: "MLC CAN Link 07",
    7718: "MLC CAN Link 08",
    7719: "MLC CAN Link 09",
    7720: "MLC CAN Link 10",
    7721: "MLC CAN Link 11",
    7722: "MLC CAN Link 12",
    7723: "MLC CAN Link 13",
    7724: "MLC CAN Link 14",
    7725: "MLC CAN Link 15",
    7726: "MLC CAN Link 16",
    7727: "MLC CAN Link 17",
    7728: "MLC CAN Link 18",
    7729: "MLC CAN Link 19",
    7730: "MLC CAN Link 20",
    7731: "MLC CAN Link 21",
    7732: "MLC CAN Link 22",
    7733: "MLC CAN Link 23",
    7734: "MLC CAN Link 24",
    7735: "MLC CAN Link 25",
    7736: "MLC CAN Link 26",
    7737: "MLC CAN Link 27",
    7738: "MLC CAN Link 28",
    7739: "MLC CAN Link 29",
    7740: "MLC CAN Link 30",
    7741: "MLC CAN Link 31",
    7750: "Gantry Pos",
    7751: "DRot Pos",
    7752: "Tbl Isoc Rot Pos",
    7753: "Tbl Long Pos",
    7754: "Tbl Lat Pos",
    7755: "Tbl Height Pos",
    7800: "No Video Image",
    7801: "Fixed Video Image",
    7802: "Bounds limit",
    7803: "Opcode",
    7804: "Framegrabber Error",
    7805: "Load calibration",
    7930: "MLC LCS Link",
    7931: "MLC Segment Mismatch",
    7932: "Message Timeout",
    7970: "Display Server Failure",
    7998: "Too Many Inhibits",
    7999: "Reset Required",
    8000: "MLC Communication Timeout",
    8001: "MLC Reset Required",
    8010: "Leaf Drive board error",
    8011: "Diaphragm Drive board error",
    8012: "DLG Drive board error",
    8020: "Leaf Move Failure",
    8021: "Diaphragm move failure",
    8022: "DLG Move Failure",
    8030: "Uncorrelated Pot DLG1",
    8031: "Uncorrelated Pot DLG2",
    8032: "Uncorrelated Pot Diaphragm 1",
    8033: "Uncorrelated Pot Diaphragm 2",
    8040: "Out of tolerance Y2 Leaves",
    8041: "Out of tolerance Y1 Leaves",
    8042: "Out of tolerance DLGs",
    8043: "Out of tolerance Diaphragms",
    8050: "Prescription Not OK",
    8051: "Beam Not Loaded",
    8101: "Loss Of Leaf Pair 1",
    8102: "Loss Of Leaf Pair 2",
    8103: "Loss Of Leaf Pair 3",
    8104: "Loss Of Leaf Pair 4",
    8105: "Loss Of Leaf Pair 5",
    8106: "Loss Of Leaf Pair 6",
    8107: "Loss Of Leaf Pair 7",
    8108: "Loss Of Leaf Pair 8",
    8109: "Loss Of Leaf Pair 9",
    8110: "Loss Of Leaf Pair 10",
    8111: "Loss Of Leaf Pair 11",
    8112: "Loss Of Leaf Pair 12",
    8113: "Loss Of Leaf Pair 13",
    8114: "Loss Of Leaf Pair 14",
    8115: "Loss Of Leaf Pair 15",
    8116: "Loss Of Leaf Pair 16",
    8117: "Loss Of Leaf Pair 17",
    8118: "Loss Of Leaf Pair 18",
    8119: "Loss Of Leaf Pair 19",
    8120: "Loss Of Leaf Pair 20",
    8121: "Loss Of Leaf Pair 21",
    8122: "Loss Of Leaf Pair 22",
    8123: "Loss Of Leaf Pair 23",
    8124: "Loss Of Leaf Pair 24",
    8125: "Loss Of Leaf Pair 25",
    8126: "Loss Of Leaf Pair 26",
    8127: "Loss Of Leaf Pair 27",
    8128: "Loss Of Leaf Pair 28",
    8129: "Loss Of Leaf Pair 29",
    8130: "Loss Of Leaf Pair 30",
    8131: "Loss Of Leaf Pair 31",
    8132: "Loss Of Leaf Pair 32",
    8133: "Loss Of Leaf Pair 33",
    8134: "Loss Of Leaf Pair 34",
    8135: "Loss Of Leaf Pair 35",
    8136: "Loss Of Leaf Pair 36",
    8137: "Loss Of Leaf Pair 37",
    8138: "Loss Of Leaf Pair 38",
    8139: "Loss Of Leaf Pair 39",
    8140: "Loss Of Leaf Pair 40",
    8141: "Loss Of Leaf Pair 41",
    8142: "Loss Of Leaf Pair 42",
    8143: "Loss Of Leaf Pair 43",
    8144: "Loss Of Leaf Pair 44",
    8145: "Loss Of Leaf Pair 45",
    8146: "Loss Of Leaf Pair 46",
    8147: "Loss Of Leaf Pair 47",
    8148: "Loss Of Leaf Pair 48",
    8149: "Loss Of Leaf Pair 49",
    8150: "Loss Of Leaf Pair 50",
    8151: "Loss Of Leaf Pair 51",
    8152: "Loss Of Leaf Pair 52",
    8153: "Loss Of Leaf Pair 53",
    8154: "Loss Of Leaf Pair 54",
    8155: "Loss Of Leaf Pair 55",
    8156: "Loss Of Leaf Pair 56",
    8157: "Loss Of Leaf Pair 57",
    8158: "Loss Of Leaf Pair 58",
    8159: "Loss Of Leaf Pair 59",
    8160: "Loss Of Leaf Pair 60",
    8161: "Loss Of Leaf Pair 61",
    8162: "Loss Of Leaf Pair 62",
    8163: "Loss Of Leaf Pair 63",
    8164: "Loss Of Leaf Pair 64",
    8165: "Loss Of Leaf Pair 65",
    8166: "Loss Of Leaf Pair 66",
    8167: "Loss Of Leaf Pair 67",
    8168: "Loss Of Leaf Pair 68",
    8169: "Loss Of Leaf Pair 69",
    8170: "Loss Of Leaf Pair 70",
    8171: "Loss Of Leaf Pair 71",
    8172: "Loss Of Leaf Pair 72",
    8173: "Loss Of Leaf Pair 73",
    8174: "Loss Of Leaf Pair 74",
    8175: "Loss Of Leaf Pair 75",
    8176: "Loss Of Leaf Pair 76",
    8177: "Loss Of Leaf Pair 77",
    8178: "Loss Of Leaf Pair 78",
    8179: "Loss Of Leaf Pair 79",
    8180: "Loss Of Leaf Pair 80",
    8200: "Low V. Coarse DLG Y1",
    8201: "High V. Coarse DLG Y1",
    8202: "Low V. Check DLG Y1",
    8203: "High V. Check DLG Y1",
    8204: "Low Ref V. Coarse DLG Y1",
    8205: "High Ref V. Coarse DLG Y1",
    8206: "Low Ref V. Check DLG Y1",
    8207: "High Ref V. Check DLG Y1",
    8208: "Sensor update Fault DLG Y1",
    8210: "Low V. Coarse DLG Y2",
    8211: "High V. Coarse DLG Y2",
    8212: "Low V. Check DLG Y2",
    8213: "High V. Check DLG Y2",
    8214: "Low Ref V. Coarse DLG Y2",
    8215: "High Ref V. Coarse DLG Y2",
    8216: "Low Ref V. Check DLG Y2",
    8217: "High Ref V. Check DLG Y2",
    8218: "Sensor update Fault DLG Y2",
    8220: "Low V. Coarse Diaphragm X1",
    8221: "High V. Coarse Diaphragm X1",
    8222: "Low V. Check Diaphragm X1",
    8223: "High V. Check Diaphragm X1",
    8224: "Low Ref V. Coarse Diaphragm X1",
    8225: "High Ref V. Coarse Diaphragm X",
    8226: "Low Ref V. Check Diaphragm X1",
    8227: "High Ref V. Check Diaphragm X1",
    8228: "Sensor update Fault Dia. X1",
    8230: "Low V. Coarse Diaphragm X2",
    8231: "High V. Coarse Diaphragm X2",
    8232: "Low V. Check Diaphragm X2",
    8233: "High V. Check Diaphragm X2",
    8234: "Low Ref V. Coarse Diaphragm X2",
    8235: "High Ref V. Coarse Dia. X2",
    8236: "Low Ref V. Check Diaphragm X2",
    8237: "High Ref V. Check Diaphragm X2",
    8238: "Sensor update Fault Dia. X2",
}


ELEKTA_LINAC_CODES: Dict[int, str] = {
    0: "Ready",
    1: "Ready",
    16: "Closed",
    34: "State Code Unknown",
    39: "Move Only",
    40: "Pause",
    41: "Intersegment",
    42: "Radiation On",
    43: "Interrupted",
    44: "Interrupted Ready",
    45: "Terminated Checking",
    46: "Terminated Ok",
    47: "Terminated Fault",
}

_LINAC_NAME_TO_CODE: Dict[str, int] = {
    "READY": 0,
    "CLOSED": 16,
    "STATE CODE UNKNOWN": 34,
    "MOVE ONLY": 39,
    "MOVE": 39,
    "PAUSE": 40,
    "INTERSEGMENT": 41,
    "RADIATION ON": 42,
    "RADIATION": 42,
    "INTERRUPTED": 43,
    "INTERUPTED": 43,
    "INTERRUPTED READY": 44,
    "INTERUPTED READY": 44,
    "TERMINATED CHECKING": 45,
    "TERMINATED OK": 46,
    "TERMINATED FAULT": 47,
}

_MLC_NAME_TO_CODE: Dict[str, int] = {
    desc.upper(): code for code, desc in ELEKTA_MLC_CODES.items()
}
_MLC_NAME_TO_CODE["MLC OK"] = 1
_MLC_NAME_TO_CODE["READY"] = 1
_MLC_NAME_TO_CODE["LEAVES NOT READY Y2"] = 7300
_MLC_NAME_TO_CODE["LEAVES NOT READY Y1"] = 7310
_MLC_NAME_TO_CODE["LEAVES NOT READY"] = 7300
_MLC_NAME_TO_CODE["MOVING"] = 7300
_MLC_NAME_TO_CODE["POSITIONING"] = 7310
_MLC_NAME_TO_CODE["REPOSITIONING"] = 7460


def format_mlc_state(raw_val: Any, default: str = "MLC OK (1)") -> str:
    """Formats an MLC state value with its integer code in parentheses, e.g. 'MLC OK (1)'.

    Args:
        raw_val: Status code integer (e.g. 1, 7300) or description string.
        default: Default return string if empty or unparseable.

    Returns:
        Formatted string: '<Description> (<Code>)' (e.g. 'Leaves not Ready Y2 (7300)').
    """
    if raw_val is None:
        return default

    # Try direct integer code
    try:
        code_int = int(float(raw_val))
        desc = ELEKTA_MLC_CODES.get(code_int, f"MLC Status {code_int}")
        return f"{desc} ({code_int})"
    except (ValueError, TypeError):
        pass

    s_val = str(raw_val).strip()
    if not s_val or s_val == "--" or s_val.lower() == "nan":
        return default

    # If it already contains parentheses with a code, return as is
    if "(" in s_val and ")" in s_val:
        return s_val

    # Special multi-bank case
    if "Y1 & Y2" in s_val.upper() or "Y1 AND Y2" in s_val.upper():
        return f"{s_val} (7300 & 7310)"

    s_upper = s_val.upper()
    if s_upper in _MLC_NAME_TO_CODE:
        code = _MLC_NAME_TO_CODE[s_upper]
        return f"{s_val} ({code})"

    return s_val


def format_linac_state(raw_val: Any, default: str = "Ready (0)") -> str:
    """Formats a Linac state value with its integer code in parentheses, e.g. 'Radiation On (42)'.

    Args:
        raw_val: Linac state integer code (e.g. 42) or description string (e.g. 'Radiation On').
        default: Default return string if empty or unparseable.

    Returns:
        Formatted string: '<Description> (<Code>)' (e.g. 'Radiation On (42)').
    """
    if raw_val is None:
        return default

    # Try direct integer code
    try:
        code_int = int(float(raw_val))
        desc = ELEKTA_LINAC_CODES.get(code_int, f"Linac State {code_int}")
        return f"{desc} ({code_int})"
    except (ValueError, TypeError):
        pass

    s_val = str(raw_val).strip()
    if not s_val or s_val == "--" or s_val.lower() == "nan":
        return default

    # If it already contains parentheses with a code, return as is
    if "(" in s_val and ")" in s_val:
        return s_val

    s_upper = s_val.upper()
    if s_upper in _LINAC_NAME_TO_CODE:
        code = _LINAC_NAME_TO_CODE[s_upper]
        return f"{s_val} ({code})"

    return s_val


def decode_mlc_status(raw_val: Any, default: str = "MLC OK (1)", include_code: bool = True) -> str:
    """Decodes a raw MLC status value to its official description, optionally including code in parentheses.

    Args:
        raw_val: Raw status code from TRF dataset (e.g. 1, 7300, 7310, 7460, 7615).
        default: Default string if code is not recognized or cannot be parsed.
        include_code: If True, returns '<Name> (<Code>)' (e.g. 'Leaves not Ready Y2 (7300)').

    Returns:
        The official Elekta MLC status name with code in parentheses.
    """
    if include_code:
        return format_mlc_state(raw_val, default=default)

    if raw_val is None:
        return default

    try:
        code_int = int(float(raw_val))
        if code_int in ELEKTA_MLC_CODES:
            return ELEKTA_MLC_CODES[code_int]
        return f"MLC Status {code_int}"
    except (ValueError, TypeError):
        pass

    s_val = str(raw_val).strip()
    if not s_val or s_val == "--" or s_val.lower() == "nan":
        return default

    for code, desc in ELEKTA_MLC_CODES.items():
        if s_val.upper() == desc.upper():
            return desc

    return s_val

