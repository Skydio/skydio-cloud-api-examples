using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Newtonsoft.Json;
using RestSharp;
using Serilog;
using SkydioInterfaceConsoleApp.Models.DB.CAD_Manual;
using SkydioInterfaceConsoleApp.ResponseBo;

namespace SkydioInterfaceConsoleApp
{
    internal class Program
    {
        static async Task Main(string[] args)
        {
            
            IConfiguration configuration = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json",true,true)
            .Build();

            var log = new LoggerConfiguration()
            .ReadFrom.Configuration(configuration)
            .CreateLogger();

            log.Information("Starting Up...");

            var apiKey = configuration["Secrets:AuthorizationAPIKey"].ToString();

            // OPEN DATA CONNECTIONS
            var services = new ServiceCollection();
            services.AddDbContext<CadContext>(options => options.UseSqlServer(configuration.GetConnectionString("CADRPT")));
            var serviceProvider = services.BuildServiceProvider();
            var CADctx = new CadContext(configuration);

            // GET CAD DATA OF ACTIVE CALLS
            var activecaddata = CADctx.Incident
                .AsNoTracking()
                .Where(x => x.inci_id != "" && x.latitude != "" && x.longitude != "" && x.latitude != "0" && x.longitude != "0")
                .ToList()
                .OrderByDescending(x=>x.inci_id);

            foreach (var caddata in activecaddata)
            {
                caddata.agency = string.IsNullOrWhiteSpace(caddata.agency) == true ? "NONE" : caddata.agency.Trim();
                caddata.agency = caddata.agency.Trim();
                caddata.inci_id = caddata.inci_id.Trim();
                caddata.service = string.IsNullOrWhiteSpace(caddata.service) == true ? "--" : caddata.service.Trim();
                caddata.naturecode = string.IsNullOrWhiteSpace(caddata.naturecode) == true ? "--" : caddata.naturecode.Trim();
                caddata.nature = string.IsNullOrWhiteSpace(caddata.nature) == true ? "NATURE NOT SET IN CAD" : caddata.nature.Trim();
            }
            
            // GET ALL MARKERS FROM SKYDIO API
            var options = new RestClientOptions("https://api.skydio.com/api/v0/markers?per_page=500&page_number=1&event_time_since=" + DateTime.Now.AddDays(-365).ToString("yyyy-MM-ddTHH:mm:ss"));
            var client = new RestClient(options);
            var requestForAllMarkers = new RestRequest("");
            requestForAllMarkers.AddHeader("accept", "application/json");
            requestForAllMarkers.AddHeader("Authorization", apiKey);
            var allMarkersResponse = await client.GetAsync(requestForAllMarkers);
            if (allMarkersResponse.IsSuccessful == false)
            {
                log.Error("Could not get all markers from skydio api.  Job Shutting down.");
                log.Error(allMarkersResponse.ErrorMessage);
                throw new Exception("Skydio api error.  Can't get all markers from api.");
            }
            var allMarkers = JsonConvert.DeserializeObject<SkydioGetMarkersResponseBo>(allMarkersResponse.Content);

            // LOOP THROUGH ALL SKYDIO MARKERS WITH SOURCE NAME "OS CAD" MARKING ANY THAT ARE NOT ACTIVE CAD CALLS FOR DELETION.
            var markersToDelete = new List<(string agency, string incidentId, string uuid)>();
            foreach (var marker in allMarkers.data.markers.Where(x=> x.source_name != null && x.source_name.StartsWith("OS CAD") == true))
            {
                var markerIncidentId = marker.marker_details.incident_id;
                var markerAgency = GetSubstringByString("[","]", marker.description);
                var activeCadIncident = activecaddata.Any(x => x.inci_id == markerIncidentId);
                //markersToDelete.Add((markerAgency, markerIncidentId, marker.uuid));
                //continue;
                if (activeCadIncident == false)
                {
                    markersToDelete.Add((markerAgency, markerIncidentId, marker.uuid));
                }
            }

            // LOOP THROUGH MARKERS MARKED FOR DELETION AND DELETE WITH SKYDIO API
            // LIMT TO 25 DELETES PER RUN.
            var tasksDelete = new List<Task<RestResponse>>();
            foreach (var markerToDelete in markersToDelete.Take(25))
            {
                options = new RestClientOptions("https://api.skydio.com/api/v0/marker/" + markerToDelete.uuid + "/delete");
                client = new RestClient(options);
                var requestDeleteMarker = new RestRequest("");
                requestDeleteMarker.AddHeader("accept", "application/json");
                requestDeleteMarker.AddHeader("Authorization", apiKey);
                var responseDeleteMarker = await client.DeleteAsync(requestDeleteMarker);
                log.Information($"Marker Deleted: IncidentId {markerToDelete.incidentId}, agency {markerToDelete.agency}, uuid {markerToDelete.uuid}");
            }
            //return;

            // CREATE OR UPDATE MARKER
            options = new RestClientOptions("https://api.skydio.com/api/v0/marker");
            client = new RestClient(options);
            var tasksCreateOrUpdate = new List<Task<RestResponse>>();

            var pagesize = 50;
            var count = activecaddata.Count();
            var pages = Math.Ceiling(((decimal)count / pagesize));
            var currentpage = 0;

            while (currentpage < pages)
            {
                tasksCreateOrUpdate.Clear();

                // CREATE LIST OF TASKS POSTING DATA TO SKYDIO
                foreach (var incident in activecaddata
                    //.Take(1)
                    .Skip(currentpage * pagesize).Take(pagesize)
                    )
                {
                    var existingMarker = allMarkers.data.markers.FirstOrDefault(x=> x.source_name == "OS CAD" &&  x.marker_details?.incident_id == incident.inci_id);

                    if (existingMarker == null)
                    {
                        var bodyObject = new SkydioCreateMarkerRequestBo();
                        bodyObject.title = incident.naturecode + " - " + incident.nature;
                        bodyObject.description = incident.service + " [" + incident.agency.Trim() + "]";
                        bodyObject.latitude = decimal.Parse(incident.latitude);
                        bodyObject.longitude = decimal.Parse(incident.longitude);
                        bodyObject.event_time = incident.calltime.Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:00");
                        bodyObject.area = incident.statbeat;
                        bodyObject.type = "INCIDENT";
                        bodyObject.marker_details.code = incident.naturecode;
                        bodyObject.marker_details.incident_id = incident.inci_id;
                        bodyObject.marker_details.priority = incident.priority;
                        bodyObject.source_name = "OS CAD";

                        var request = new RestRequest("");
                        request.AddHeader("accept", "application/json");
                        request.AddHeader("Authorization", apiKey);
                        request.AddJsonBody(JsonConvert.SerializeObject(bodyObject), false);
                        tasksCreateOrUpdate.Add(client.PostAsync(request));

                    }
                    else
                    {
                        // IF EXISTING MARKER MINUTE IS THE SAME AS THE CURRENT MINUTE THEN UPDATE.  NEED TO DO THIS BECAUSE MARKERS HAVE TO BE UPDATED AT LEAST ONCE
                        // AN HOUR AND THE MARKER DOES NOT HAVE AN UPDATE DATE TO WORK OFF OF.
                        var currentMinute = DateTime.Now.Minute;
                        // IF EXISTING MARKER MOVED THEN UPDATE IT
                        if (existingMarker.latitude != decimal.Parse(incident.latitude) 
                            || existingMarker.longitude != decimal.Parse(incident.longitude) 
                            || DateTime.Parse(existingMarker.event_time).Minute == currentMinute
                            || existingMarker.marker_details.code != incident.naturecode)
                        {
                            var bodyObject = new SkydioUpdateMarkerRequestBo();
                            bodyObject.title = incident.naturecode + " - " + incident.nature;
                            bodyObject.description = incident.service + " [" + incident.agency.Trim() + "]";
                            bodyObject.latitude = decimal.Parse(incident.latitude);
                            bodyObject.longitude = decimal.Parse(incident.longitude);
                            bodyObject.event_time = incident.calltime.Value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:00");
                            bodyObject.area = incident.statbeat;
                            bodyObject.type = "INCIDENT";
                            bodyObject.marker_details.code = incident.naturecode;
                            bodyObject.marker_details.incident_id = incident.inci_id;
                            bodyObject.marker_details.priority = incident.priority;
                            bodyObject.source_name = "OS CAD";
                            bodyObject.uuid = existingMarker.uuid;

                            var request = new RestRequest("");
                            request.AddHeader("accept", "application/json");
                            request.AddHeader("Authorization", apiKey);
                            request.AddJsonBody(JsonConvert.SerializeObject(bodyObject), false);
                            tasksCreateOrUpdate.Add(client.PostAsync(request));
                        }

                    }

                }

                // RUN AND WAIT FOR ALL TO COMPLETE
                Task.WaitAll(tasksCreateOrUpdate.ToArray());

                // LOOP THROUGH RESULTS SO UUID'S CAN GET LOGGED
                foreach (var task in tasksCreateOrUpdate)
                {
                    if (task.Result != null && task.Result.IsSuccessful == true)
                    {
                        var responseObject = JsonConvert.DeserializeObject<SkydioUpsertMarkerResponseBo>(task.Result.Content);
                        var responseMarkerAgency = responseObject.data.marker.source_name.Split(' ').Last();

                        var existingMarker = allMarkers.data.markers.FirstOrDefault(x => x.source_name == "OS CAD" 
                            && x.marker_details?.incident_id == responseObject.data.marker.marker_details.incident_id);

                        if (existingMarker == null)
                        {
                            log.Information($"Marker created: IncidentId {responseObject.data.marker.marker_details.incident_id}, agency {responseMarkerAgency}, uuid {responseObject.data.marker.uuid}");
                        }
                        else
                        {
                            log.Information($"Marker updated: IncidentId {responseObject.data.marker.marker_details.incident_id}, agency {responseMarkerAgency}, uuid {responseObject.data.marker.uuid}");
                        }
                    }
                    else
                    {
                        log.Error("Add/Update Marker with Skydio API failed");
                        log.Error(task.Result.ErrorMessage);
                    }

                }

                currentpage += 1;
                log.Information("Page " + currentpage.ToString() + " processed.");

            }
            
            log.Information("Ended...");
        }

        internal static string GetSubstringByString(string a, string b, string c)
        {
            return c.Substring((c.IndexOf(a) + a.Length), (c.IndexOf(b) - c.IndexOf(a) - a.Length));
        }
    }
}
