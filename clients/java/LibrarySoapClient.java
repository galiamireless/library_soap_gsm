import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public final class LibrarySoapClient {
    private static final String ENDPOINT = "http://127.0.0.1:5000/soap";
    private static final String SOAP = "http://schemas.xmlsoap.org/soap/envelope/";
    private static final String NS = "urn:udem:library:classifier";

    static String pending(String clientId) throws Exception {
        String xml = "<?xml version=\"1.0\"?><soap:Envelope xmlns:soap=\"" + SOAP + "\" xmlns:tns=\"" + NS + "\"><soap:Body><tns:ObtenerConceptosPendientes><tns:clientType>java-client</tns:clientType><tns:clientId>" + clientId + "</tns:clientId></tns:ObtenerConceptosPendientes></soap:Body></soap:Envelope>";
        HttpRequest request = HttpRequest.newBuilder(URI.create(ENDPOINT)).header("Content-Type", "text/xml").POST(HttpRequest.BodyPublishers.ofString(xml)).build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception { System.out.println(pending("java-demo")); }
}
