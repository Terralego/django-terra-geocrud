def render_relation(relation, qs):
    # get property displayed list
    body = ""

    head = '<th style="width: 90%;">Nom</th><th style="width: 10%;">Lien</th>'

    for obj in qs:
        line = f"<td>{obj.properties.get('name', obj.identifier)}</td>"
        # add url
        line = f'{line}<td><a href="/CRUD/map/{relation.destination.name}/{obj.identifier}/">lien</a></td>'
        body = f"{body}<tr>{line}</tr>"

    return f'<table style="width: 100%;"><thead>{head}</thead><tbody>{body}</tbody></table>' if qs else None
