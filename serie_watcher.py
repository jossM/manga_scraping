import click

import page_marks_db
from skraper import skraper_orc


@click.command()
@click.argument('serie_id')
@click.option('--name', default=None, help='The name of the serie you want displayed.')
@click.option('--img', default=None, help='The image of the serie you want displayed.')
@click.option('--keep_chapters/--delete_chapters', default=True, help='Whether to keep the chapters already present in db.')
def add_serie_in_db(serie_id, name=None, img=None, keep_chapters=True):
    """ called only in local for admin tasks """
    new_page_mark = None
    if keep_chapters:
        new_page_mark = page_marks_db.get(serie_id)
        click.echo(f"retrieved {new_page_mark}")
        if new_page_mark is not None:
            if name is not None:
                new_page_mark.serie_name = name
            if img is not None:
                new_page_mark.img_link = img
    if new_page_mark is None:
        new_page_mark = skraper_orc.scrap_bakaupdate_serie(serie_id, name, img)
    click.echo(f"stored {new_page_mark}")
    page_marks_db.put(new_page_mark)


if __name__ == "__main__":
    ## called only in local for admin tasks
    add_serie_in_db()
