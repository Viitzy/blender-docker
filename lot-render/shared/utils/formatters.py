def unmask_phone(phone: str):
    if phone[0] == "0":
        phone = phone[1:]
    return (
        phone.replace("(", "")
        .replace(")", "")
        .replace("-", "")
        .replace(" ", "")
        .replace("+", "")
    ).strip()


def mask_phone(phone: str):
    if (phone.startswith("55") or phone.startswith("+55")) and len(phone) >= 13:
        return f"({phone[2:4]}) {phone[4:9]}-{phone[9:]}"
    elif len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"
    else:
        return phone
