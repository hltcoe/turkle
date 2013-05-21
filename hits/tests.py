# -*- coding: utf-8 -*-
from io import BytesIO
from django.test import TestCase
from models import Hit, HitTemplate
from management.commands.dump_results import results_data
from management.commands.publish_hits import parse_csv_file
import unittest


class TestModels(TestCase):

    def setUp(self):
        form = HitTemplate(form="<p></p>")
        form.save()
        hit = Hit(
            source_file="",
            source_line=1,
            form=form,
            input_csv_fields="",
            input_csv_values="",
            answers='{"comment": "\u221e", "userDisplayLanguage": "",'
            '"sentence_textbox_3_verb1": "", "city": "",'
            '"sentence_textbox_1_verb6": "", "sentence_textbox_1_verb7": "",'
            '"sentence_textbox_1_verb4": "", "sentence_textbox_1_verb5": "",'
            '"sentence_textbox_1_verb2": "", "sentence_textbox_1_verb3": "",'
            '"sentence_textbox_1_verb1": "", "sentence_textbox_2_verb4": "",'
            '"csrfmiddlewaretoken": "7zxQ9Yyug6Nsnm4nLky9p8ObJwNipdu8",'
            '"sentence_drop_2_verb3": "blank", "sentence_drop_2_verb2":'
            '"blank", "sentence_drop_2_verb1": "blank",'
            '"sentence_textbox_2_verb1": "", "sentence_textbox_2_verb3": "",'
            '"sentence_drop_2_verb4": "blank", "sentence_textbox_2_verb2":'
            '"", "submitit": "Submit", "browserInfo": "",'
            '"sentence_drop_1_verb1": "blank", "sentence_drop_1_verb2":'
            '"blank", "sentence_drop_1_verb3": "blank",'
            '"sentence_drop_1_verb4": "blank", "sentence_drop_1_verb5":'
            '"blank", "sentence_drop_1_verb6": "blank",'
            '"sentence_drop_1_verb7": "blank", "country": "",'
            '"sentence_drop_3_verb1": "blank", "ipAddress": "", "region":""}',
            completed=True,
        )
        hit.save()
        self.hit = hit

    def test_new_hit(self):
        """
        unicode() should be the template's title followed by :id of the hit.
        """
        self.assertEqual('HIT id:1', unicode(self.hit))

    def test_result_to_dict_Answer(self):
        hit = self.hit
        self.assertEqual(
            'blank',
            hit.results_to_dict()['sentence_drop_1_verb1']
        )

    def test_result_to_dict_ignore_csrfmiddlewaretoken(self):
        with self.assertRaises(KeyError):
            self.hit.results_to_dict()['Answer.csrfmiddlewaretoken']

    def test_result_to_dict_should_include_inputs(self):
        hit = self.hit
        self.assertEqual(
            'blank',
            hit.results_to_dict()['sentence_drop_1_verb1']
        )

    def test_result_to_dict_unicode(self):
        hit = self.hit
        self.assertEqual(
            unicode('∞', encoding='utf-8'),
            hit.results_to_dict()['comment']
        )

    def test_unicode_through_dump_results(self):
        self.assertEqual(1, len(Hit.objects.filter(completed=True)))
        _, rows = results_data(Hit.objects.filter(completed=True))
        self.assertEqual(
            unicode('∞', encoding='utf-8'),
            #rows[0][u'Answer.comment'].encode('latin-1').decode('utf-8')
            rows[0]['Answer.comment']
        )


class TestGenerateForm(TestCase):

    def setUp(self):
        self.hit_template = HitTemplate(
                source_file="filepath",
                form="""
<p>
<meta charset="utf-8">
<table cellspacing="0" cellpadding="6" border="1">
    <tbody>
        <tr>
            <td style="text-align: center; "><b>TWEET 1</b></td>
            <td style="text-align: center; ">Marque <input type="checkbox" name="tweet0_notlang" /> si el mensaje no est&aacute; en espa&ntilde;ol.  Pase al siguiente Tweet.</td>
        </tr>
        <tr>
            <td colspan="2" style="text-align: center; "><span style="font-family: 'Comic Sans MS'; ">${tweet0_before_entity}<span style="color: rgb(0, 0, 255); ">${tweet0_entity}</span>${tweet0_after_entity}</span></td>
        </tr>
        <tr>
            <td colspan="2">
            <p>1. La persona twitteando&nbsp;<select name="tweet0_sentiment" onchange="checkToAddWords0(this.value)">
            <option value="">&nbsp;</option>
            <option value="neutral">no expresa un sentimiento</option>
            <option value="positive">expresa un sentimiento positivo</option>
            <option value="negative">expresa un sentimiento negativo</option>
            <option value="both">expresa a la vez un sentimiento positivo y un sentimiento negativo</option>
            </select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">${tweet0_entity}</span> en este mensaje.</p>
            </td>
        </tr>
        <tr>
            <td colspan="2" id="tweet0_sureness">
            <div id="tweet0_sure_expand" style="">
            <p><span grey="">2.&nbsp;Elige su nivel de confianza&nbsp;... </span></p>
            </div>
            </td>
        </tr>
        <tr>
            <td colspan="2" id="tweet0_words">
            <div id="tweet0_words_minimize" style="">
            <p><span grey="">3. Para cada palabra a continuaci&oacute;n ...</span></p>
            </div>
            </td>
        </tr>
    </tbody>
</table>
</meta>
</p>
"""
        )
        self.hit_template.save()
        self.hit = Hit(
            source_file = "filepath",
            source_line = 1,
            form=self.hit_template,
            input_csv_fields="tweet0_id,tweet0_entity,tweet0_before_entity,tweet0_after_entity,tweet0_word0,tweet0_word1,tweet0_word2,tweet1_id,tweet1_entity,tweet1_before_entity,tweet1_after_entity,tweet1_word0,tweet1_word1,tweet1_word2,tweet2_id,tweet2_entity,tweet2_before_entity,tweet2_after_entity,tweet2_word0,tweet2_word1,tweet2_word2,tweet3_id,tweet3_entity,tweet3_before_entity,tweet3_after_entity,tweet3_word0,tweet3_word1,tweet3_word2,tweet4_id,tweet4_entity,tweet4_before_entity,tweet4_after_entity,tweet4_word0,tweet4_word1,tweet4_word2,tweet5_id,tweet5_entity,tweet5_before_entity,tweet5_after_entity,tweet5_word0,tweet5_word1,tweet5_word2",
            input_csv_values="268,SANTOS, Muy bien America ......... y lo siento mucho , un muy buen rival,mucho,&nbsp;,&nbsp;,2472,GREGORY, Ah bueno , tampoco andes pidiendo ese tipo de milagros . @jcabrerac @CarlosCabreraR,bueno,&nbsp;,&nbsp;,478,ALEJANDRO, @aguillen19 &#44; un super abrazo mi querido , &#44; mis mejores deseos para este 2012 ... muakkk !,querido,&nbsp;,&nbsp;,906_control, PF, Acusan camioneros extorsiones de, : Transportistas acusaron que deben pagar entre 13 y 15 mil pesos a agentes que .. http://t.co/d8LUVvhP,acusaron,&nbsp;,&nbsp;,2793_control, CHICARO, Me gusta cuando chicharo hace su oracion es lo que lo hace especial .,&nbsp;,gusta,&nbsp;,&nbsp;,357,OSCAR WILDE&QUOT;, &quot; @ ifilosofia : Las pequeñas acciones de cada día son las que hacen o deshacen el carácter.&quot; , bueno !!!! Es así,bueno,&nbsp;,&nbsp;",
        )
        self.hit.save()

    def test_generate_form(self):
        expect = """
<p>
<meta charset="utf-8">
<table cellspacing="0" cellpadding="6" border="1">
    <tbody>
        <tr>
            <td style="text-align: center; "><b>TWEET 1</b></td>
            <td style="text-align: center; ">Marque <input type="checkbox" name="tweet0_notlang" /> si el mensaje no est&aacute; en espa&ntilde;ol.  Pase al siguiente Tweet.</td>
        </tr>
        <tr>
            <td colspan="2" style="text-align: center; "><span style="font-family: 'Comic Sans MS'; ">Muy bien America ......... y lo siento mucho<span style="color: rgb(0, 0, 255); ">SANTOS</span>un muy buen rival</span></td>
        </tr>
        <tr>
            <td colspan="2">
            <p>1. La persona twitteando&nbsp;<select name="tweet0_sentiment" onchange="checkToAddWords0(this.value)">
            <option value="">&nbsp;</option>
            <option value="neutral">no expresa un sentimiento</option>
            <option value="positive">expresa un sentimiento positivo</option>
            <option value="negative">expresa un sentimiento negativo</option>
            <option value="both">expresa a la vez un sentimiento positivo y un sentimiento negativo</option>
            </select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">SANTOS</span> en este mensaje.</p>
            </td>
        </tr>
        <tr>
            <td colspan="2" id="tweet0_sureness">
            <div id="tweet0_sure_expand" style="">
            <p><span grey="">2.&nbsp;Elige su nivel de confianza&nbsp;... </span></p>
            </div>
            </td>
        </tr>
        <tr>
            <td colspan="2" id="tweet0_words">
            <div id="tweet0_words_minimize" style="">
            <p><span grey="">3. Para cada palabra a continuaci&oacute;n ...</span></p>
            </div>
            </td>
        </tr>
    </tbody>
</table>
</meta>
</p>
"""
        actual = self.hit.generate_form()
        self.assertEqual(expect, actual)

    def test_map_fields_csv_row(self):
        hit_template = HitTemplate(
            source_file="filepath",
            form="""</select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">${tweet0_entity}</span> en este mensaje.</p>"""
        )
        hit_template.save()
        hit = Hit(
            source_file = "filepath",
            source_line = 1,
            form=hit_template,
            input_csv_fields="tweet0_id,tweet0_entity",
            input_csv_values="268,SANTOS"
        )
        hit.save()
        expect = """</select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">SANTOS</span> en este mensaje.</p>"""
        actual = hit.generate_form()
        self.assertEqual(expect, actual)

    def test_quotes_in_csv_header_row(self):
        hit_template = HitTemplate(
            source_file="filepath",
            form="""</select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">${tweet0_entity}</span> en este mensaje.</p>"""
        )
        hit_template.save()
        hit = Hit(
            source_file="filepath",
            source_line=1,
            form=hit_template,
            input_csv_fields='"tweet0_id", "tweet0_entity"',
            input_csv_values='"906_control", " PF"',
        )
        hit.save()
        expect = {'tweet0_id': '906_control', 'tweet0_entity': ' PF'}
        actual = hit.inputs_to_dict()
        self.assertEqual(expect, actual)


class TestPublishHits(TestCase):

    def setUp(self):
        csv_text = (
            u'h0,h1\r\n'
            u'"é0",ñ0\r\n'
            u'"é1, e1",ñ1'
        )
        self.csv_file = BytesIO(csv_text.encode('utf8'))

    def test_parse_csv_file(self):
        header, data_rows = parse_csv_file(self.csv_file)
        self.assertEqual(
            [u'h0', u'h1'],
            header
        )
        self.assertEqual(
            [
                [u'é0', u'ñ0'],
                [u'é1, e1', u'ñ1'],
            ],
            [row for row in data_rows]
        )

    @unittest.skip('')
    def test_create_template_from_html_file(self):
        pass
