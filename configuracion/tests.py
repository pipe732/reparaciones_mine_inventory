from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from configuracion.views import configuracion_view


class ConfiguracionViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_guardar_configuracion_nube_persiste_database_url(self):
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / '.env'

            request = self.factory.post(
                '/configuracion/',
                {
                    'almacenamiento': 'nube',
                    'database_url': 'postgresql://neon_user:secret@ep-xxx.us-east-1.aws.neon.tech:5432/neondb?sslmode=require',
                },
            )
            session_middleware = SessionMiddleware(lambda req: None)
            session_middleware.process_request(request)
            request.session['usuario_documento'] = '12345678'
            request.session['usuario_rol'] = 'administrador'
            request.session.save()

            message_middleware = MessageMiddleware(lambda req: None)
            message_middleware.process_request(request)

            with patch('configuracion.views.ENV_PATH', env_path):
                response = configuracion_view(request)

            self.assertEqual(response.status_code, 302)
            contenido = env_path.read_text(encoding='utf-8')
            self.assertIn('DB_ENGINE=nube', contenido)
            self.assertIn('DATABASE_URL=postgresql://neon_user:secret@ep-xxx.us-east-1.aws.neon.tech:5432/neondb?sslmode=require', contenido)

    def test_guardar_configuracion_local_preserva_database_url(self):
        with TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / '.env'
            # Pre-populate env file with a database url
            env_path.write_text(
                "DB_ENGINE=nube\nDATABASE_URL=postgresql://existing_url:5432/neondb\n",
                encoding='utf-8'
            )

            request = self.factory.post(
                '/configuracion/',
                {
                    'almacenamiento': 'local',
                    'database_url': '',
                },
            )
            session_middleware = SessionMiddleware(lambda req: None)
            session_middleware.process_request(request)
            request.session['usuario_documento'] = '12345678'
            request.session['usuario_rol'] = 'administrador'
            request.session.save()

            message_middleware = MessageMiddleware(lambda req: None)
            message_middleware.process_request(request)

            with patch('configuracion.views.ENV_PATH', env_path):
                response = configuracion_view(request)

            self.assertEqual(response.status_code, 302)
            contenido = env_path.read_text(encoding='utf-8')
            self.assertIn('DB_ENGINE=local', contenido)
            # The existing DATABASE_URL should be preserved and not erased
            self.assertIn('DATABASE_URL=postgresql://existing_url:5432/neondb', contenido)
