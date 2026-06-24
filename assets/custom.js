window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        getLocation: function(n_clicks) {
            if (!n_clicks) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
            return new Promise(function(resolve, reject) {
                if (!navigator.geolocation) {
                    alert("Geolocation is blocked on HTTP by the browser. Please read the instructions to bypass it.");
                    resolve([window.dash_clientside.no_update, window.dash_clientside.no_update]);
                } else {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            resolve([position.coords.latitude, position.coords.longitude]);
                        },
                        function(error) {
                            alert("Unable to retrieve your location. Check permissions or HTTP connection restrictions.");
                            resolve([window.dash_clientside.no_update, window.dash_clientside.no_update]);
                        },
                        { enableHighAccuracy: true } // Richiede maggiore precisione per i telefoni
                    );
                }
            });
        }
    }
});