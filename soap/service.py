import logging
from xml.etree import ElementTree as ET

from db.repository import ConceptNotFoundError, DatabaseRepository, DuplicateClassificationError
from soap.envelope import child_text, envelope, parse_request
from soap.faults import SoapError, soap_fault
from soap.security import configured_users, read_username_token, verify_password

LOGGER = logging.getLogger(__name__)
VALID_MODELS = {"IaaS", "PaaS", "SaaS", "FaaS"}


class SoapService:
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository

    def handle(self, xml_bytes: bytes) -> tuple[bytes, int]:
        try:
            operation, header, payload = parse_request(xml_bytes)
            if operation == "ObtenerConceptosPendientes":
                data = self.repository.list_pending_concepts(
                    child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerConceptosPendientesResponse", data, "concepts"), 200
            if operation == "RegistrarClasificacion":
                data = self._classification_payload(payload)
                result = self.repository.register_classification(data)
                return envelope("RegistrarClasificacionResponse", result), 200
            if operation == "ObtenerProgresoUsuario":
                result = self.repository.get_user_progress(
                    child_text(payload, "email"), child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerProgresoUsuarioResponse", result), 200
            if operation == "ObtenerEstadisticasPorModelo":
                self._authenticate(header)
                result = self.repository.get_statistics(
                    child_text(payload, "clientType"), child_text(payload, "clientId")
                )
                return envelope("ObtenerEstadisticasPorModeloResponse", result, "statistics"), 200
            raise SoapError("La operación solicitada no está disponible.", status=400)
        except ET.ParseError:
            return soap_fault("soap:Client", "XML inválido.", "Verifique el SOAP Envelope."), 400
        except SoapError as error:
            return soap_fault(error.code, str(error), error.detail), error.status
        except (ValueError, KeyError) as error:
            return soap_fault("soap:Client", str(error)), 400
        except ConceptNotFoundError:
            return soap_fault("soap:Client", "El concepto indicado no existe para el libro especificado."), 400
        except DuplicateClassificationError:
            return soap_fault("soap:Client", "La clasificación ya existe para este clasificador y concepto.", "CONFLICT_409"), 409
        except Exception:
            LOGGER.exception("Falla interna procesando solicitud SOAP")
            return soap_fault("soap:Server", "No fue posible procesar la solicitud."), 500

    @staticmethod
    def _classification_payload(payload: ET.Element) -> dict:
        model = child_text(payload, "model")
        if model not in VALID_MODELS:
            raise SoapError("El modelo Cloud debe ser IaaS, PaaS, SaaS o FaaS.", status=400)
        try:
            concept_id = int(child_text(payload, "conceptId"))
        except (TypeError, ValueError) as error:
            raise SoapError("conceptId debe ser un entero.", status=400) from error
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

    @staticmethod
    def _authenticate(header: ET.Element) -> None:
        token = read_username_token(header)
        users = configured_users()
        if token is None or token[0] not in users or not verify_password(token[1], users[token[0]]):
            raise SoapError("Autenticación WS-Security inválida.", code="soap:Client", status=401, detail="AUTHENTICATION_FAILED")
