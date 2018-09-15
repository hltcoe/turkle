# -*- coding: utf-8 -*-
from cStringIO import StringIO
import os.path

import django.test

from hits.models import Hit, HitBatch, HitTemplate


class TestHitBatch(django.test.TestCase):

    def test_hit_batch_to_csv(self):
        hit_template = HitTemplate(name='test', form='<p>${number} - ${letter}</p>')
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        hit_one = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'number': '1', 'letter': 'a'},
            answers={'combined': '1a'}
        ).save()
        hit_two = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'number': '2', 'letter': 'b'},
            answers={'combined': '2b'}
        ).save()

        csv_output = StringIO()
        hit_batch.to_csv(csv_output)
        self.assertEqual(
            '"Input.letter","Input.number","Answer.combined"\r\n' +
            '"b","2","2b"\r\n' +
            '"a","1","1a"\r\n',
            csv_output.getvalue()
        )

    def test_hit_batch_to_csv_variable_number_of_answers(self):
        hit_template = HitTemplate(name='test', form='<p>${letter}</p>')
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        hit_one = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'a'},
            answers={'1': 1, '2': 2}
        ).save()
        hit_two = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'b'},
            answers={'3': 3, '4': 4}
        ).save()
        hit_three = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'c'},
            answers={'3': 3, '2': 2}
        ).save()

        csv_output = StringIO()
        hit_batch.to_csv(csv_output)
        rows = csv_output.getvalue().split()
        self.assertEqual(rows[0], '"Input.letter","Answer.1","Answer.2","Answer.3","Answer.4"')
        self.assertTrue('"a","1","2","",""' in rows)
        self.assertTrue('"b","","","3","4"' in rows)
        self.assertTrue('"c","","2","3",""' in rows)


    def test_hit_batch_from_emoji_csv(self):
        hit_template = HitTemplate(name='test', form='<p>${emoji} - ${more-emoji}</p>')
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()

        csv_fh = open(os.path.abspath('hits/tests/resources/emoji.csv'))
        hit_batch.create_hits_from_csv(csv_fh)

        self.assertEqual(hit_batch.total_hits(), 3)
        hits = hit_batch.hit_set.all()
        self.assertEqual(hits[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(hits[0].input_csv_fields['more-emoji'], u'😃')
        self.assertEqual(hits[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(hits[2].input_csv_fields['more-emoji'], u'🤭')


class TestModels(django.test.TestCase):

    def setUp(self):
        """
        Sets up HitTemplate, Hit objects, and saves them to the DB.
        The HitTemplate form HTML only displays the one input variable.
        The Hit has inputs and answers and refers to the HitTemplate form.
        """
        hit_template = HitTemplate(name='test', form="<p>${foo}</p>")
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()

        hit = Hit(
            hit_batch=hit_batch,
            input_csv_fields={u'foo': u'bar'},
            answers={
                u"comment": u"\u221e", u"userDisplayLanguage": u"",
                u"sentence_textbox_3_verb1": u"", u"city": u"",
                u"sentence_textbox_1_verb6": u"",
                u"sentence_textbox_1_verb7": u"",
                u"sentence_textbox_1_verb4": u"",
                u"sentence_textbox_1_verb5": u"",
                u"sentence_textbox_1_verb2": u"",
                u"sentence_textbox_1_verb3": u"",
                u"sentence_textbox_1_verb1": u"",
                u"sentence_textbox_2_verb4": u"",
                u"csrfmiddlewaretoken": u"7zxQ9Yyug6Nsnm4nLky9p8ObJwNipdu8",
                u"sentence_drop_2_verb3": u"foo",
                u"sentence_drop_2_verb2": u"foo",
                u"sentence_drop_2_verb1": u"foo",
                u"sentence_textbox_2_verb1": u"",
                u"sentence_textbox_2_verb3": u"",
                u"sentence_drop_2_verb4": u"foo",
                u"sentence_textbox_2_verb2": u"",
                u"submitit": u"Submit", u"browserInfo": u"",
                u"sentence_drop_1_verb1": u"foo",
                u"sentence_drop_1_verb2": u"foo",
                u"sentence_drop_1_verb3": u"foo",
                u"sentence_drop_1_verb4": u"foo",
                u"sentence_drop_1_verb5": u"foo",
                u"sentence_drop_1_verb6": u"foo",
                u"sentence_drop_1_verb7": u"foo", u"country": u"",
                u"sentence_drop_3_verb1": u"foo",
                u"ipAddress": u"", u"region": u""
            },
            completed=True,
        )
        hit.save()
        self.hit = hit

    def test_extract_fieldnames_from_form_html(self):
        self.assertEqual(
            {u'foo': True},
            self.hit.hit_batch.hit_template.fieldnames
        )

        hit_template = HitTemplate(name='test', form='<p>${foo} - ${bar}</p>')
        hit_template.save()
        self.assertEqual(
            {u'foo': True, u'bar': True},
            hit_template.fieldnames
        )

    def test_hit_template_to_csv(self):
        hit_template = HitTemplate(name='test', form='<p>${number} - ${letter}</p>')
        hit_template.save()
        hit_batch_one = HitBatch(hit_template=hit_template)
        hit_batch_one.save()
        hit_one = Hit(
            hit_batch=hit_batch_one,
            completed=True,
            input_csv_fields={'number': '1', 'letter': 'a'},
            answers={'combined': '1a'}
        ).save()
        hit_batch_two = HitBatch(hit_template=hit_template)
        hit_batch_two.save()
        hit_two = Hit(
            hit_batch=hit_batch_two,
            completed=True,
            input_csv_fields={'number': '2', 'letter': 'b'},
            answers={'combined': '2b'}
        ).save()

        csv_output = StringIO()
        hit_template.to_csv(csv_output)

        rows = csv_output.getvalue().split('\r\n')
        self.assertEqual(
            '"Input.letter","Input.number","Answer.combined"',
            rows[0]
        )
        self.assertTrue('"a","1","1a"' in rows[1:])
        self.assertTrue('"b","2","2b"' in rows[1:])

    def test_hit_template_to_csv_different_answers_per_batch(self):
        hit_template = HitTemplate(name='test', form='<p>${letter}</p>')
        hit_template.save()
        hit_batch_one = HitBatch(hit_template=hit_template)
        hit_batch_one.save()
        hit_one = Hit(
            hit_batch=hit_batch_one,
            completed=True,
            input_csv_fields={'letter': 'a'},
            answers={'1': 1, '2': 2}
        ).save()
        hit_batch_two = HitBatch(hit_template=hit_template)
        hit_batch_two.save()
        hit_two = Hit(
            hit_batch=hit_batch_two,
            completed=True,
            input_csv_fields={'letter': 'b'},
            answers={'3': 3, '4': 4}
        ).save()

        csv_output = StringIO()
        hit_template.to_csv(csv_output)

        rows = csv_output.getvalue().split('\r\n')
        self.assertEqual(
            '"Input.letter","Answer.1","Answer.2","Answer.3","Answer.4"',
            rows[0]
        )
        self.assertTrue('"a","1","2","",""' in rows)
        self.assertTrue('"b","","","3","4"' in rows)

    def test_new_hit(self):
        """
        unicode(hit) should return the template's title followed by :id of the
        hit.
        """
        self.assertEqual('HIT id:1', unicode(self.hit))

    def test_result_to_dict_Answer(self):
        hit = self.hit
        self.assertEqual(
            'foo',
            hit.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_ignore_csrfmiddlewaretoken(self):
        with self.assertRaises(KeyError):
            self.hit.answers['Answer.csrfmiddlewaretoken']

    def test_result_to_dict_should_include_inputs(self):
        hit = self.hit
        self.assertEqual(
            'foo',
            hit.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_unicode(self):
        hit = self.hit
        self.assertEqual(
            '∞'.decode('utf-8'),
            hit.answers['comment']
        )


class TestGenerateForm(django.test.TestCase):

    def setUp(self):
        with open('hits/tests/resources/form_0.html') as f:
            form = f.read().decode('utf-8')

        self.hit_template = HitTemplate(name="filepath", form=form)
        self.hit_template.save()
        self.hit_batch = HitBatch(hit_template=self.hit_template)
        self.hit_batch.save()
        field_names = u"tweet0_id,tweet0_entity,tweet0_before_entity,tweet0_after_entity,tweet0_word0,tweet0_word1,tweet0_word2,tweet1_id,tweet1_entity,tweet1_before_entity,tweet1_after_entity,tweet1_word0,tweet1_word1,tweet1_word2,tweet2_id,tweet2_entity,tweet2_before_entity,tweet2_after_entity,tweet2_word0,tweet2_word1,tweet2_word2,tweet3_id,tweet3_entity,tweet3_before_entity,tweet3_after_entity,tweet3_word0,tweet3_word1,tweet3_word2,tweet4_id,tweet4_entity,tweet4_before_entity,tweet4_after_entity,tweet4_word0,tweet4_word1,tweet4_word2,tweet5_id,tweet5_entity,tweet5_before_entity,tweet5_after_entity,tweet5_word0,tweet5_word1,tweet5_word2",
        values = u"268,SANTOS, Muy bien America ......... y lo siento mucho , un muy buen rival,mucho,&nbsp;,&nbsp;,2472,GREGORY, Ah bueno , tampoco andes pidiendo ese tipo de milagros . @jcabrerac @CarlosCabreraR,bueno,&nbsp;,&nbsp;,478,ALEJANDRO, @aguillen19 &#44; un super abrazo mi querido , &#44; mis mejores deseos para este 2012 ... muakkk !,querido,&nbsp;,&nbsp;,906_control, PF, Acusan camioneros extorsiones de, : Transportistas acusaron que deben pagar entre 13 y 15 mil pesos a agentes que .. http://t.co/d8LUVvhP,acusaron,&nbsp;,&nbsp;,2793_control, CHICARO, Me gusta cuando chicharo hace su oracion es lo que lo hace especial .,&nbsp;,gusta,&nbsp;,&nbsp;,357,OSCAR WILDE&QUOT;, &quot; @ ifilosofia : Las pequeñas acciones de cada día son las que hacen o deshacen el carácter.&quot; , bueno !!!! Es así,bueno,&nbsp;,&nbsp;",
        self.hit = Hit(
            hit_batch=self.hit_batch,
            input_csv_fields=dict(zip(field_names, values))
        )
        self.hit.save()

    def test_generate_form(self):
        with open('hits/tests/resources/form_0_filled.html') as f:
            form = f.read().decode('utf-8')
        expect = form
        actual = self.hit.generate_form()
        self.assertNotEqual(expect, actual)

    def test_map_fields_csv_row(self):
        hit_template = HitTemplate(
            name='test',
            form=u"""</select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">${tweet0_entity}</span> en este mensaje.</p>"""
        )
        hit_template.save()
        hit_batch = HitBatch(hit_template=hit_template)
        hit_batch.save()
        hit = Hit(
            hit_batch=hit_batch,
            input_csv_fields=dict(
                zip(
                    [u"tweet0_id", u"tweet0_entity"],
                    [u"268", u"SANTOS"],
                )
            ),
        )
        hit.save()
        expect = u"""<div style=" width:100%; border:2px solid black; margin-top:10px"><div style="margin:10px"></select> con relaci&oacute;n a <span style="color: rgb(0, 0, 255);">SANTOS</span> en este mensaje.</p></div></div>"""
        actual = hit.generate_form()
        self.assertEqual(expect, actual)


__all__ = (
    'TestGenerateForm',
    'TestModels',
)
