/* OPBConfig is for all the hooks that the core.js calls */
OPBConfig = {
	enableGphoto2: false,

	// To do on loading (dom complete)
	onLoad : function () {
		OpenPhotoBooth.openSet();
		jQuery( '#countdown' ).click(function(e) {
			OPBSkin.startCapture();
		});
	},

	onUnload: function () {
		OpenPhotoBooth.closeSet();
	},

	// Fired when Sound Manager 2 is loaded & ready
	onSoundLoad: function () {
	},

	// Fired immediately before a capture request is sent to the SWF
	preCapture : function () {
	},

	// Fired immediately after a capture is returned from the SWF and POSTed to the server
	postCapture : function ( json ) {
		$( "#countdown" ).text( "" );
		++OPBSkin.captured;
		$( '#photo' + OPBSkin.captured ).attr( 'src', OPBThumbPath + json.thumbnail );
		if( OPBSkin.captured >= 4 ) {
			OpenPhotoBooth.closeSet();
			OpenPhotoBooth.openSet();
			$( "#countdown" ).html( "All Done! Thanks!" );
			setTimeout( "OPBSkin.reset();", 5000 );
		}
		else
			setTimeout( "OPBSkin.countDown( 4, 1000 );", 1000 );
	},

	// Fired when a key is pressed
	onKeyPress: function (e) {
	}
};

/* OPBSkin is a place to safely store functions for just your skin */
OPBSkin = {
	// How many have we captured?
	captured: 0,

	// Are we "in" a set?
	inSet: false,

	// These hold soundmanager 2 sounds
	shutter: null,
	beep: null,

	countDown: function (count, interval) {
		--count;
		if(count == 0) {
			$( "#countdown" ).text( "Smile!" );
			setTimeout( "OpenPhotoBooth.capture();", 10 );
		}
		else {
			$( "#countdown" ).text( count );
			setTimeout("OPBSkin.countDown("+count+","+interval+");",interval);
		}
	},

	reset: function () {
	 OPBSkin.captured = 0;
	 $( "#countdown" ).text( "Touch here to start" );
	 OPBSkin.inSet = false;
	 for( i = 1; i <= 4; ++i ) { $( "#photo" + i ).attr( "src", OPBSkinPath + "set" + i + ".jpg"); }
	},

	startCapture: function() {
                OPBSkin.inSet = true;
                OPBSkin.countDown (6, 1000);
        }
};
