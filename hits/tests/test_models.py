# -*- coding: utf-8 -*-
try:
    from cStringIO import StringIO
except ImportError:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import BytesIO
        StringIO = BytesIO

import os.path

from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import ValidationError
import django.test

from hits.models import Hit, HitAssignment, HitBatch, HitProject

# hack to add unicode() to python3 for backward compatibility
try:
    unicode('')
except NameError:
    unicode = str


class TestHitAssignment(django.test.TestCase):
    def test_hit_marked_as_completed(self):
        # When assignment_per_hit==1, completing 1 Assignment marks Task as complete
        hit_project = HitProject(name='test', html_template='<p>${number} - ${letter}</p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()

        hit = Hit(
            hit_batch=hit_batch,
            input_csv_fields={'number': '1', 'letter': 'a'}
        )
        hit.save()

        self.assertEqual(hit_batch.assignments_per_hit, 1)
        self.assertFalse(hit.completed)

        HitAssignment(
            assigned_to=None,
            completed=True,
            hit=hit
        ).save()

        hit.refresh_from_db()
        self.assertTrue(hit.completed)

    def test_hit_marked_as_completed_two_way_redundancy(self):
        # When assignment_per_hit==2, completing 2 Assignments marks Task as complete
        hit_project = HitProject(name='test', html_template='<p>${number} - ${letter}</p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.assignments_per_hit = 2
        hit_batch.save()

        hit = Hit(
            hit_batch=hit_batch,
            input_csv_fields={'number': '1', 'letter': 'a'}
        )
        hit.save()

        self.assertFalse(hit.completed)

        HitAssignment(
            assigned_to=None,
            completed=True,
            hit=hit
        ).save()
        hit.refresh_from_db()
        self.assertFalse(hit.completed)

        HitAssignment(
            assigned_to=None,
            completed=True,
            hit=hit
        ).save()
        hit.refresh_from_db()
        self.assertTrue(hit.completed)


class TestHitBatch(django.test.TestCase):

    def test_hit_batch_to_csv(self):
        hit_project = HitProject(name='test', html_template='<p>${number} - ${letter}</p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()

        hit1 = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )
        hit1.save()
        HitAssignment(
            answers={'combined': '1a'},
            assigned_to=None,
            completed=True,
            hit=hit1
        ).save()

        hit2 = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'number': '2', 'letter': 'b'},
        )
        hit2.save()
        HitAssignment(
            answers={'combined': '2b'},
            assigned_to=None,
            completed=True,
            hit=hit2
        ).save()

        csv_output = StringIO()
        hit_batch.to_csv(csv_output)
        self.assertEqual(
            b'"Input.letter","Input.number","Answer.combined"\r\n' +
            b'"b","2","2b"\r\n' +
            b'"a","1","1a"\r\n',
            csv_output.getvalue()
        )

    def test_hit_batch_to_csv_variable_number_of_answers(self):
        hit_project = HitProject(name='test', html_template='<p>${letter}</p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()

        hit1 = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'a'},
        )
        hit1.save()
        HitAssignment(
            answers={'1': 1, '2': 2},
            assigned_to=None,
            completed=True,
            hit=hit1,
        ).save()

        hit2 = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'b'},
        )
        hit2.save()
        HitAssignment(
            answers={'3': 3, '4': 4},
            assigned_to=None,
            completed=True,
            hit=hit2
        ).save()

        hit3 = Hit(
            hit_batch=hit_batch,
            completed=True,
            input_csv_fields={'letter': 'c'},
        )
        hit3.save()
        HitAssignment(
            answers={'3': 3, '2': 2},
            assigned_to=None,
            completed=True,
            hit=hit3
        ).save()

        csv_output = StringIO()
        hit_batch.to_csv(csv_output)
        rows = csv_output.getvalue().split()
        self.assertEqual(rows[0], b'"Input.letter","Answer.1","Answer.2","Answer.3","Answer.4"')
        self.assertTrue(b'"a","1","2","",""' in rows)
        self.assertTrue(b'"b","","","3","4"' in rows)
        self.assertTrue(b'"c","","2","3",""' in rows)

    def test_hit_batch_from_emoji_csv(self):
        hit_project = HitProject(name='test', html_template='<p>${emoji} - ${more_emoji}</p>')
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()

        csv_fh = open(os.path.abspath('hits/tests/resources/emoji.csv'), 'rb')
        hit_batch.create_hits_from_csv(csv_fh)

        self.assertEqual(hit_batch.total_hits(), 3)
        hits = hit_batch.hit_set.all()
        self.assertEqual(hits[0].input_csv_fields['emoji'], u'😀')
        self.assertEqual(hits[0].input_csv_fields['more_emoji'], u'😃')
        self.assertEqual(hits[2].input_csv_fields['emoji'], u'🤔')
        self.assertEqual(hits[2].input_csv_fields['more_emoji'], u'🤭')

    def test_login_required_validation_1(self):
        # No ValidationError thrown
        hit_project = HitProject(
            login_required=False,
        )
        hit_project.save()
        HitBatch(
            assignments_per_hit=1,
            hit_project=hit_project,
        ).clean()

    def test_login_required_validation_2(self):
        # No ValidationError thrown
        hit_project = HitProject(
            login_required=True,
        )
        hit_project.save()
        HitBatch(
            assignments_per_hit=2,
            hit_project=hit_project,
        ).clean()

    def test_login_required_validation_3(self):
        with self.assertRaisesMessage(ValidationError, 'Assignments per Task must be 1'):
            hit_project = HitProject(
                login_required=False,
            )
            hit_project.save()
            HitBatch(
                assignments_per_hit=2,
                hit_project=hit_project,
            ).clean()


class TestHitBatchAvailableHITs(django.test.TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='secret')

        self.hit_project = HitProject(name='test', html_template='<p>${number} - ${letter}</p>')
        self.hit_project.save()

    def test_available_hits_for__aph_is_1(self):
        hit_batch = HitBatch(
            assignments_per_hit=1,
            hit_project=self.hit_project
        )
        hit_batch.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 0)
        self.assertEqual(hit_batch.next_available_hit_for(self.user), None)

        hit = Hit(
            hit_batch=hit_batch,
        )
        hit.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 1)
        self.assertEqual(hit_batch.next_available_hit_for(self.user), hit)

        hit_assignment = HitAssignment(
            assigned_to=self.user,
            completed=False,
            hit=hit,
        )
        hit_assignment.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 0)
        self.assertEqual(hit_batch.next_available_hit_for(self.user), None)

    def test_available_hits_for__aph_is_2(self):
        hit_batch = HitBatch(
            assignments_per_hit=2,
            hit_project=self.hit_project
        )
        hit_batch.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 0)

        hit = Hit(
            hit_batch=hit_batch,
        )
        hit.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 1)

        hit_assignment = HitAssignment(
            assigned_to=self.user,
            completed=False,
            hit=hit,
        )
        hit_assignment.save()
        self.assertEqual(hit_batch.total_available_hits_for(self.user), 0)

        other_user = User.objects.create_user('other_user', password='secret')
        self.assertEqual(hit_batch.total_available_hits_for(other_user), 1)

        hit_assignment = HitAssignment(
            assigned_to=other_user,
            completed=False,
            hit=hit,
        )
        hit_assignment.save()
        self.assertEqual(hit_batch.total_available_hits_for(other_user), 0)

    def test_available_hits_for_anon_user(self):
        anonymous_user = AnonymousUser()
        user = User.objects.create_user('user', password='secret')

        hit_project_protected = HitProject(
            active=True,
            login_required=True,
        )
        hit_project_protected.save()
        self.assertEqual(len(HitProject.available_for(anonymous_user)), 0)
        self.assertEqual(len(HitProject.available_for(user)), 2)  # HitProject created by setUp
        hit_batch_protected = HitBatch(hit_project=hit_project_protected)
        hit_batch_protected.save()
        Hit(hit_batch=hit_batch_protected).save()
        self.assertEqual(len(hit_batch_protected.available_hits_for(anonymous_user)), 0)
        self.assertEqual(len(hit_batch_protected.available_hits_for(user)), 1)

        hit_project_unprotected = HitProject(
            active=True,
            login_required=False,
        )
        hit_project_unprotected.save()
        hit_batch_unprotected = HitBatch(hit_project=hit_project_unprotected)
        hit_batch_unprotected.save()
        Hit(hit_batch=hit_batch_unprotected).save()
        self.assertEqual(len(HitProject.available_for(anonymous_user)), 1)
        self.assertEqual(len(HitProject.available_for(user)), 3)
        self.assertEqual(len(hit_project_unprotected.batches_available_for(anonymous_user)), 1)
        self.assertEqual(len(hit_project_unprotected.batches_available_for(user)), 1)
        self.assertEqual(len(hit_batch_unprotected.available_hits_for(anonymous_user)), 1)
        self.assertEqual(len(hit_batch_unprotected.available_hits_for(user)), 1)


class TestHitProject(django.test.TestCase):

    def test_available_for_active_flag(self):
        user = User.objects.create_user('testuser', password='secret')

        self.assertEqual(len(HitProject.available_for(user)), 0)

        HitProject(
            active=False,
        ).save()
        self.assertEqual(len(HitProject.available_for(user)), 0)

        HitProject(
            active=True,
        ).save()
        self.assertEqual(len(HitProject.available_for(user)), 1)

    def test_available_for_login_required(self):
        anonymous_user = AnonymousUser()

        self.assertEqual(len(HitProject.available_for(anonymous_user)), 0)

        HitProject(
            login_required=True,
        ).save()
        self.assertEqual(len(HitProject.available_for(anonymous_user)), 0)

        authenticated_user = User.objects.create_user('testuser', password='secret')
        self.assertEqual(len(HitProject.available_for(authenticated_user)), 1)

    def test_batches_available_for(self):
        user = User.objects.create_user('testuser', password='secret')

        hit_project = HitProject(
            active=True,
        )
        hit_project.save()
        self.assertEqual(len(hit_project.batches_available_for(user)), 0)

        HitBatch(
            active=False,
            hit_project=hit_project,
        ).save()
        self.assertEqual(len(hit_project.batches_available_for(user)), 0)

        HitBatch(
            active=True,
            hit_project=hit_project,
        ).save()
        self.assertEqual(len(hit_project.batches_available_for(user)), 1)

    def test_batches_available_for_anon(self):
        anonymous_user = AnonymousUser()

        hit_project_protected = HitProject(
            active=True,
            login_required=True,
        )
        hit_project_protected.save()
        self.assertEqual(len(hit_project_protected.batches_available_for(anonymous_user)), 0)

        HitBatch(hit_project=hit_project_protected).save()
        self.assertEqual(len(hit_project_protected.batches_available_for(anonymous_user)), 0)

        hit_project_unprotected = HitProject(
            active=True,
            login_required=False,
        )
        hit_project_unprotected.save()
        self.assertEqual(len(hit_project_unprotected.batches_available_for(anonymous_user)), 0)

        HitBatch(hit_project=hit_project_unprotected).save()
        self.assertEqual(len(hit_project_unprotected.batches_available_for(anonymous_user)), 1)

    def test_form_with_submit_button(self):
        hit_project = HitProject(
            html_template='<p><input id="my_submit_button" type="submit" value="MySubmit" /></p>'
        )
        hit_project.save()
        self.assertTrue(hit_project.html_template_has_submit_button)

    def test_form_without_submit_button(self):
        hit_project = HitProject(
            html_template='<p>Quick brown fox</p>'
        )
        hit_project.save()
        self.assertFalse(hit_project.html_template_has_submit_button)

    def test_login_required_validation_1(self):
        # No ValidationError thrown
        HitProject(
            assignments_per_hit=1,
            login_required=False,
        ).clean()

    def test_login_required_validation_2(self):
        # No ValidationError thrown
        HitProject(
            assignments_per_hit=2,
            login_required=True,
        ).clean()

    def test_login_required_validation_3(self):
        with self.assertRaisesMessage(ValidationError, 'Assignments per Task must be 1'):
            HitProject(
                assignments_per_hit=2,
                login_required=False,
            ).clean()


class TestModels(django.test.TestCase):

    def setUp(self):
        """
        Sets up HitProject, Hit objects, and saves them to the DB.
        The HitProject form HTML only displays the one input variable.
        The Hit has inputs and answers and refers to the HitProject form.
        """
        hit_project = HitProject(name='test', html_template="<p>${foo}</p>")
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
        hit_batch.save()

        hit = Hit(
            hit_batch=hit_batch,
            input_csv_fields={u'foo': u'bar'},
            completed=True,
        )
        hit.save()
        self.hit = hit

        self.hit_assignment = HitAssignment(
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
            assigned_to=None,
            completed=True,
            hit=hit
        )
        self.hit_assignment.save()

    def test_extract_fieldnames_from_form_html(self):
        self.assertEqual(
            {u'foo': True},
            self.hit.hit_batch.hit_project.fieldnames
        )

        hit_project = HitProject(name='test', html_template='<p>${foo} - ${bar}</p>')
        hit_project.save()
        self.assertEqual(
            {u'foo': True, u'bar': True},
            hit_project.fieldnames
        )

    def test_hit_project_to_csv(self):
        hit_project = HitProject(name='test', html_template='<p>${number} - ${letter}</p>')
        hit_project.save()
        hit_batch_one = HitBatch(hit_project=hit_project)
        hit_batch_one.save()

        hit1 = Hit(
            hit_batch=hit_batch_one,
            completed=True,
            input_csv_fields={'number': '1', 'letter': 'a'},
        )
        hit1.save()
        HitAssignment(
            answers={'combined': '1a'},
            assigned_to=None,
            completed=True,
            hit=hit1
        ).save()

        hit_batch_two = HitBatch(hit_project=hit_project)
        hit_batch_two.save()
        hit2 = Hit(
            hit_batch=hit_batch_two,
            completed=True,
            input_csv_fields={'number': '2', 'letter': 'b'}
        )
        hit2.save()
        HitAssignment(
            answers={'combined': '2b'},
            assigned_to=None,
            completed=True,
            hit=hit2
        ).save()

        csv_output = StringIO()
        hit_project.to_csv(csv_output)

        rows = csv_output.getvalue().split(b'\r\n')
        self.assertEqual(
            b'"Input.letter","Input.number","Answer.combined"',
            rows[0]
        )
        self.assertTrue(b'"a","1","1a"' in rows[1:])
        self.assertTrue(b'"b","2","2b"' in rows[1:])

    def test_hit_project_to_csv_different_answers_per_batch(self):
        hit_project = HitProject(name='test', html_template='<p>${letter}</p>')
        hit_project.save()
        hit_batch_one = HitBatch(hit_project=hit_project)
        hit_batch_one.save()

        hit1 = Hit(
            hit_batch=hit_batch_one,
            completed=True,
            input_csv_fields={'letter': 'a'},
        )
        hit1.save()
        HitAssignment(
            answers={'1': 1, '2': 2},
            assigned_to=None,
            completed=True,
            hit=hit1
        ).save()

        hit_batch_two = HitBatch(hit_project=hit_project)
        hit_batch_two.save()
        hit2 = Hit(
            hit_batch=hit_batch_two,
            completed=True,
            input_csv_fields={'letter': 'b'},
        )
        hit2.save()
        HitAssignment(
            answers={'3': 3, '4': 4},
            assigned_to=None,
            completed=True,
            hit=hit2
        ).save()

        csv_output = StringIO()
        hit_project.to_csv(csv_output)

        rows = csv_output.getvalue().split(b'\r\n')
        self.assertEqual(
            b'"Input.letter","Answer.1","Answer.2","Answer.3","Answer.4"',
            rows[0]
        )
        self.assertTrue(b'"a","1","2","",""' in rows)
        self.assertTrue(b'"b","","","3","4"' in rows)

    def test_new_hit(self):
        """
        unicode(hit) should return the template's title followed by :id of the
        hit.
        """
        self.assertEqual('Task id:1', unicode(self.hit))

    def test_result_to_dict_Answer(self):
        self.assertEqual(
            'foo',
            self.hit_assignment.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_ignore_csrfmiddlewaretoken(self):
        with self.assertRaises(KeyError):
            self.hit_assignment.answers['Answer.csrfmiddlewaretoken']

    def test_result_to_dict_should_include_inputs(self):
        self.assertEqual(
            'foo',
            self.hit_assignment.answers['sentence_drop_1_verb1']
        )

    def test_result_to_dict_unicode(self):
        self.assertEqual(
            u'∞',
            self.hit_assignment.answers['comment']
        )


class TestGenerateForm(django.test.TestCase):

    def setUp(self):
        with open('hits/tests/resources/form_0.html') as f:
            html_template = f.read()
            # python 2 compat hack
            try:
                html_template = html_template.decode('utf-8')
            except AttributeError:
                pass

        self.hit_project = HitProject(name="filepath", html_template=html_template)
        self.hit_project.save()
        self.hit_batch = HitBatch(hit_project=self.hit_project)
        self.hit_batch.save()
        field_names = u"tweet0_id,tweet0_entity,tweet0_before_entity,tweet0_after_entity," + \
            u"tweet0_word0,tweet0_word1,tweet0_word2,tweet1_id,tweet1_entity," + \
            u"tweet1_before_entity,tweet1_after_entity,tweet1_word0,tweet1_word1,tweet1_word2," + \
            u"tweet2_id,tweet2_entity,tweet2_before_entity,tweet2_after_entity,tweet2_word0," + \
            u"tweet2_word1,tweet2_word2,tweet3_id,tweet3_entity,tweet3_before_entity," + \
            u"tweet3_after_entity,tweet3_word0,tweet3_word1,tweet3_word2,tweet4_id," + \
            u"tweet4_entity,tweet4_before_entity,tweet4_after_entity,tweet4_word0," + \
            u"tweet4_word1,tweet4_word2,tweet5_id,tweet5_entity,tweet5_before_entity," + \
            u"tweet5_after_entity,tweet5_word0,tweet5_word1,tweet5_word2",
        values = u"268,SANTOS, Muy bien America ......... y lo siento mucho , un muy buen " + \
            u"rival,mucho,&nbsp;,&nbsp;,2472,GREGORY, Ah bueno , tampoco andes pidiendo ese " +\
            u"tipo de milagros . @jcabrerac @CarlosCabreraR,bueno,&nbsp;,&nbsp;,478,ALEJANDRO," + \
            u" @aguillen19 &#44; un super abrazo mi querido , &#44; mis mejores deseos para " + \
            u"este 2012 ... muakkk !,querido,&nbsp;,&nbsp;,906_control, PF, Acusan camioneros " + \
            u"extorsiones de, : Transportistas acusaron que deben pagar entre 13 y 15 mil " + \
            u"pesos a agentes que .. http://t.co/d8LUVvhP,acusaron,&nbsp;,&nbsp;,2793_control," + \
            u" CHICARO, Me gusta cuando chicharo hace su oracion es lo que lo hace especial .," + \
            u"&nbsp;,gusta,&nbsp;,&nbsp;,357,OSCAR WILDE&QUOT;, &quot; @ ifilosofia : Las " + \
            u"pequeñas acciones de cada día son las que hacen o deshacen el carácter.&quot; , " + \
            u"bueno !!!! Es así,bueno,&nbsp;,&nbsp;",
        self.hit = Hit(
            hit_batch=self.hit_batch,
            input_csv_fields=dict(zip(field_names, values))
        )
        self.hit.save()

    def test_populate_html_template(self):
        with open('hits/tests/resources/form_0_filled.html') as f:
            form = f.read()
            # python 2 compat hack
            try:
                form = form.decode('utf-8')
            except AttributeError:
                pass

        expect = form
        actual = self.hit.populate_html_template()
        self.assertNotEqual(expect, actual)

    def test_map_fields_csv_row(self):
        hit_project = HitProject(
            name='test',
            html_template=u"""</select> con relaci&oacute;n a """ +
            u"""<span style="color: rgb(0, 0, 255);">""" +
            u"""${tweet0_entity}</span> en este mensaje.</p>"""
        )
        hit_project.save()
        hit_batch = HitBatch(hit_project=hit_project)
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
        expect = u"""</select> con relaci&oacute;n a <span style="color:""" + \
            u""" rgb(0, 0, 255);">SANTOS</span> en este mensaje.</p>"""
        actual = hit.populate_html_template()
        self.assertEqual(expect, actual)


__all__ = (
    'TestGenerateForm',
    'TestModels',
)
