import click

import page_marks_db
from img_hosting import delete_image


@click.command()
@click.argument('serie_id')
def delete_serie(serie_id):
    """ called only in local for admin tasks """
    page_mark = page_marks_db.get(serie_id)
    if page_mark is None:
        click.echo(f"Serie {serie_id} not found in db. Stopping here.")
        return
    click.confirm(f"Do you want to delete {repr(page_mark)} ?", abort=True)
    delete_image(serie_id=serie_id)
    page_marks_db.delete(serie_id)
    click.echo(f"Done")


if __name__ == "__main__":
    ## called only in local for admin tasks
    delete_serie()
