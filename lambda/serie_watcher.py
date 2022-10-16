import datetime
import io

import click
import inquirer
from PIL import Image

import mangaupdate_srv
import page_marks_db
from releases_types import Serie
from img_hosting import expose_image


@click.command()
@click.option('--keep_chapters/--delete_chapters', default=True, help='Whether to keep the chapters already present in db.')
def add_serie_in_db(keep_chapters=True):
    """ called only in local for admin tasks """
    serie_id: str = None
    selected_serie: Serie = None
    image: Image = None
    while True:
        search = click.prompt("Search keywords ", type=str)
        series = mangaupdate_srv.search_series(search)
        series = {s.serie_id: s for s in series}
        question_key = "serie_id"
        answers = inquirer.prompt([
            inquirer.List(
                name=question_key,
                message="select the corresponding series",
                choices=[
                    inquirer.questions.TaggedValue(label=s.serie_name, value=s.serie_id)
                    for s in series.values()
                ]
            )
        ])
        if not answers:
            continue
        serie_id = answers[question_key]
        selected_serie = series[serie_id]
        image = Image.open(io.BytesIO(mangaupdate_srv.get_image(selected_serie.img_url)))
        image.show(title=selected_serie.serie_name)
        if click.confirm("Does the image correspond ?"):
            break
    default_serie_name = selected_serie.serie_name

    chapter_marks = None
    if keep_chapters:
        previous_page_mark = page_marks_db.get(serie_id)
        if previous_page_mark is not None:
            click.echo(f"retrieved from db : {previous_page_mark}")
            default_serie_name = previous_page_mark.serie_name
            chapter_marks = previous_page_mark.chapter_marks
    serie_name_key = "serie_name"
    release_history = "release_history"
    image_file_path_key = "image_file_path"
    answers = inquirer.prompt([
        inquirer.Text(
            name=serie_name_key,
            message="Choose the name to be searched after each release",
            default=default_serie_name,),
        inquirer.Confirm(
            name=release_history,
            message="Add already published chapters to db",
            default=False,),
        inquirer.Text(
            name=image_file_path_key,
            message="Enter local file path to the image associated with the serie",
            default=None, ),
    ])
    click.echo(f"Retrieving info and storing them in db.")

    image_file_path = answers.get(image_file_path_key)
    if image_file_path:
        image = Image.open(image_file_path)
    if image_file_path or chapter_marks is None:
        expose_image(serie_id=serie_id, image=image)

    if not answers[release_history]:
        chapter_marks = []
    elif not chapter_marks:
        scrapped_page_mark = mangaupdate_srv.get_releases(datetime.date.today() - datetime.timedelta(days=7))
        try:
            chapter_marks = next(
                serie_release.releases for serie_release in scrapped_page_mark
                if serie_release.serie_id == selected_serie.serie_id
            )
        except StopIteration:
            chapter_marks = []

    new_page_mark = page_marks_db.PageMark(
        serie_id=serie_id,
        serie_name=answers[serie_name_key],
        chapter_marks=chapter_marks,
    )
    click.echo(f"stored {new_page_mark}")
    page_marks_db.put(new_page_mark)


if __name__ == "__main__":
    ## called only in local for admin tasks
    add_serie_in_db()
