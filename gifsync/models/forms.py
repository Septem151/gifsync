from flask_wtf import FlaskForm
from wtforms import FileField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class GifCreationForm(FlaskForm):
    gif_file = FileField("Choose File")
    gif_name = StringField(
        "Name your creation", validators=[DataRequired(), Length(min=1, max=64)]
    )
    beats_per_loop = IntegerField(
        "Beats per loop", validators=[DataRequired(), NumberRange(1, 64)]
    )
    submit = SubmitField("PRESTO!")


class PreferencesForm(FlaskForm):
    min_tempo = IntegerField(
        "Minimum Tempo", validators=[Optional(), NumberRange(min=0)]
    )
    max_tempo = IntegerField(
        "Maximum Tempo", validators=[Optional(), NumberRange(min=0)]
    )
    submit = SubmitField("Save")
