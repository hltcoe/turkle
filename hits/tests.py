from django.test import TestCase
from models import Hit, HitTemplate


class TestModels(TestCase):

    def setUp(self):
        form = HitTemplate(form="<p></p>")
        form.save()
        hit = Hit(
                source_file = "",
                source_line = 1,
                form=form,
                input_csv_fields="",
                input_csv_values="",
        )
        hit.save()
        self.hit = hit

    def test_new_hit(self):
        """
        unicode() should be the template's title followed by :id of the hit.
        """
        self.assertEqual('HIT id:1', unicode(self.hit))

    def test_result_to_dict(self):
        hit = self.hit
        hit.answers="csrfmiddlewaretoken=7zxQ9Yyug6Nsnm4nLky9p8ObJwNipdu8&sentence_drop_1_verb1=blank&sentence_drop_1_verb2=blank&sentence_drop_1_verb3=blank&sentence_drop_1_verb4=blank&sentence_drop_1_verb5=blank&sentence_drop_1_verb6=blank&sentence_drop_1_verb7=blank&sentence_textbox_1_verb1=&sentence_textbox_1_verb2=&sentence_textbox_1_verb3=&sentence_textbox_1_verb4=&sentence_textbox_1_verb5=&sentence_textbox_1_verb6=&sentence_textbox_1_verb7=&sentence_drop_2_verb1=blank&sentence_drop_2_verb2=blank&sentence_drop_2_verb3=blank&sentence_drop_2_verb4=blank&sentence_textbox_2_verb1=&sentence_textbox_2_verb2=&sentence_textbox_2_verb3=&sentence_textbox_2_verb4=&sentence_drop_3_verb1=blank&sentence_textbox_3_verb1=&comment=+&submitit=Submit&userDisplayLanguage=&browserInfo=&ipAddress=&country=&city=&region="
        hit.save()
        self.assertEqual(
                "blank",
                hit.result_to_dict()['Answer.sentence_drop_1_verb1']
        )
