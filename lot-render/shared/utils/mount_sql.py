def mount_update_query(data: dict):
    query = ""
    for key in data.keys():
        query += f"{key} = %({key})s, "

    query = query[:-2]
    return query
