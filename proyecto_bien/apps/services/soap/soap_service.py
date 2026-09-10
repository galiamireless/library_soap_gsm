"""SOAP use cases for Cloud concept classification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
from xml.etree import ElementTree as ET

try:
    from .repository import ConceptNotFoundError, DuplicateClassificationError
    from .soap_codec import child_text, envelope, fault, parse_request
except ImportError:  # Allows direct execution from the service directory.
    from repository import ConceptNotFoundError, DuplicateClassificationError
    from soap_codec import child_text, envelope, fault, parse_request


LOGGER = logging.getLogger(__name__)
WSSE_NS = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
VALID_MODELS = {"IaaS", "PaaS", "SaaS", "FaaS"}


class SoapError(Exception):
    def __init__(self, message: str, code: str = "soap:Client", status: int = 400, detail: str | None = None):
        super().__init__(message)
        self.code = code
        self.status = status
        self.detail = detail


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def _verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(base64.b64encode(digest).decode(), expected)
    except (TypeError, ValueError):
        return False


def _configured_users() -> dict[str, str]:
    result = {}
    for entry in os.getenv("SOAP_USER_HASHES", "").split(","):
        if ":" in entry:
            name, encoded = entry.split(":", 1)
            result[name.strip()] = encoded.strip()
    return result


def _authenticate(header: ET.Element) -> None:
    token = header.find(f".//{{{WSSE_NS}}}UsernameToken")
    username = token.findtext(f"{{{WSSE_NS}}}Username") if token is not None else None
    password = token.findtext(f"{{{WSSE_NS}}}Password") if token is not None else None
    users = _configured_users()
    if not username or not password or username not in users or not _verify_password(password, users[username]):
        raise SoapError("Autenticación WS-Security inválida.", status=401, detail="AUTHENTICATION_FAILED")


class SoapService:
    def __init__(self, repository):
        self.repository = repository

    def handle(self, xml_bytes: bytes) -> tuple[bytes, int]:
        try:
            operation, header, payload = parse_request(xml_bytes)
            if operation == "ObtenerConceptosPendientes":
                result = self.repository.list_pending_concepts(
                    child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerConceptosPendientesResponse", result, "concepts"), 200
            if operation == "RegistrarClasificacion":
                result = self.repository.register_classification(self._classification_payload(payload))
                return envelope("RegistrarClasificacionResponse", result), 200
            if operation == "ObtenerProgresoUsuario":
                result = self.repository.get_user_progress(
                    child_text(payload, "email"), child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerProgresoUsuarioResponse", result), 200
            if operation == "ObtenerEstadisticasPorModelo":
                _authenticate(header)
                result = self.repository.get_statistics(
                    child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerEstadisticasPorModeloResponse", result, "statistics"), 200
            raise SoapError("La operación solicitada no está disponible.", status=400)
        except ET.ParseError:
            return fault("soap:Client", "XML inválido.", "Verifique el SOAP Envelope."), 400
        except SoapError as error:
            return fault(error.code, str(error), error.detail), error.status
        except (ValueError, KeyError) as error:
            return fault("soap:Client", str(error)), 400
        except ConceptNotFoundError:
            return fault("soap:Client", "El concepto indicado no existe para el libro especificado."), 400
        except DuplicateClassificationError:
            return fault("soap:Client", "La clasificación ya existe para este clasificador y concepto.", "CONFLICT_409"), 409
        except Exception:
            LOGGER.exception("Falla interna procesando solicitud SOAP")
            return fault("soap:Server", "No fue posible procesar la solicitud."), 500

    @staticmethod
    def _classification_payload(payload: ET.Element) -> dict:
        model = child_text(payload, "model")
        if model not in VALID_MODELS:
            raise SoapError("El modelo Cloud debe ser IaaS, PaaS, SaaS o FaaS.")
        try:
            concept_id = int(child_text(payload, "conceptId"))
        except (TypeError, ValueError) as error:
            raise SoapError("conceptId debe ser un entero.") from error
        return {
            "first_name": child_text(payload, "firstName"),
            "last_name": child_text(payload, "lastName"),
            "email": child_text(payload, "email"),
            "concept_id": concept_id,
            "isbn": child_text(payload, "isbn"),
            "model": model,
            "client_type": child_text(payload, "clientType"),
            "client_id": child_text(payload, "clientId"),
        }
