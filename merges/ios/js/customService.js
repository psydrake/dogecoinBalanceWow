// platform-specific service
angular.module('app.customService', []).
    factory('customService', function($timeout) {
		// custom functions for iOS

        return {
			openLink: function(link) {
				// Use in-app browser for iOS
				if (link && link.match(/^mailto:/)) {
					window.open(encodeURI(link)); 
				}
				else {
					window.open(encodeURI(link), '_blank', 'location=yes'); 
				}
			},

			trackPage: function(page) {
				$timeout(function() {
					if (typeof analytics !== "undefined") {
						analytics.trackView(page);
					}
				}, 1500);
			},

			doCustomActions: function() {
				$timeout(function() {
					if (typeof analytics !== "undefined") {
						analytics.startTrackerWithId('UA-48620823-2');
					}
				}, 1000);
			}
		}
	});


