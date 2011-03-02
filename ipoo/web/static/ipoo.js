/*jslint white: false, browser: true, devel: true, undef: true, nomen: true, eqeqeq: true, bitwise: true, regexp: true, newcap: true, maxerr: 50 */
/*global
XPathResult,GM_xmlhttpRequest
*/

var ipoo = function () {

    var ipoo = {};              // Future ipoo namespace
    /******************************************************
     * Configuration stuff
     */   
    ipoo.config = {
        ws: "",                 // Address of IPoo web service
        icon: "static/ipoo-round.png",
        skin: "static/ipooChrome.html",
        height: 250,            // Panel height
        width: "35em",          // Width of one subpanel
        id: "IPooUI",
	greasemonkey: false	// Run from greasemonkey?
    };

    /******************************************************
     * Helper functions
     */

    /**
     * Helper function to handle logging. This uses Firebug console if
     * present.
     */
    var fbconsole = function ()
    {
        var names = ["log", "debug", "info", "warn", "error"];
        var i, that = {};
        
        function callFirebugConsole(f) {
            return function () {
                if (typeof console !== "undefined" && console[f] && console[f].apply) {
                    return console[f].apply(console, arguments);
                }
            };
        }
        for (i = 0; i < names.length; ++i) {
            that[names[i]] = callFirebugConsole(names[i]);
        }

        return that;
    }();

    /**
     * Helper function to do an XMLHttpRequest and retrieve a arbitrary text
     * object from it. We take a request as a string, a success
     * callback and an error callback. Success callback is called with
     * JSON data. Error callback will be given a reason as argument.
     */
    var getText = function (request, success, error)
    {

        function dataReceived(response)
        {
            if (response.readyState === 4) {
                if (response.status !== 200) {
                    error(response.status ? ("got status " +
					     response.status) : "network error");
                    return;
                }
                success(response.responseText);
            }
        }

        var client;
	if (typeof GM_xmlhttpRequest === "function") {
	    // We are inside greasemonkey
	    client = GM_xmlhttpRequest({
		method: "GET",
		url: ipoo.config.ws + request,
		onload: dataReceived
	    });
	} else {
	    client = new XMLHttpRequest();
            client.onreadystatechange = function() {
		dataReceived(client);
	    };
            client.open("GET", ipoo.config.ws + request);
            client.send();
	}
    };

    /**
     * Helper function to do an XMLHttpRequest and retrieve a JSON
     * object from it. We take a request as a string, a success
     * callback and an error callback. Success callback is called with
     * JSON data. Error callback will be given a reason as argument.
     */
    var getJSON = function (request, success, error)
    {
        getText(request, function (json) {
            try {
                json = JSON.parse(json);
            } catch (e) {
                error("unable to parse result");
                return;
            }
            success(json);
        }, error);
    };

    /******************************************************
     * Application logic (but private)
     */

    var chrome = null;

    /**
     * Function to query IPoo for a give IP or hostname. It takes a string
     * who will be used to query IPoo.
     */
    var query = function (query)
    {
        var panel;
        query = query.replace(/\u200b/g, '');
        fbconsole.info("ipoo: Process query " + query);

        panel = chrome.panel.subpanel();
        panel.title(query);
        panel.loading();
        getJSON("api/1.0/q/" + encodeURIComponent(query) + "/",
                function (properties) {
                    // We need to query all available properties (one
                    // by one)
                    var names = [];
                    var property;
                    for (property in properties) {
                        if (typeof properties[property] !== 'function') {
                            names.push(property);
                        }
                    }
                    if (!names.length) {
                        panel.info("No information available about this query.");
                        panel.complete();
                        return;
                    }
                    return function queryNextProperty() {
                        var name = names.pop();
                        if (!name) {
                            panel.complete();
                            return;
                        }
                        panel.section(properties[name]);
                        getJSON("api/1.0/q/" + encodeURIComponent(query) + "/" +
                                encodeURIComponent(name) + "/",
                                function (result) {
                                    panel.pretty(result);
                                    queryNextProperty();
                                },
                                function (reason) {
                                    panel.error("Unable to query this property: " + reason);
                                    queryNextProperty();
                                });
                    }();
                },
                function (reason) {
                    panel.error("Unable to get the list of available properties: " + reason);
                    panel.complete();
                });
    };

    /**
     * Function to turn IP and hostnames to links to IPoo panel. It
     * takes a DOM object that will be used as a start point to find
     * hostnames and IP addresses. If hyperlinks is defined, use
     * hyperlink instead of icon.
     */
    var linkify = function (container, document, hyperlinks)
    {
        var notInTags = ['head', 'noscript', 'option', 'script', 'style', 'title', 'textarea'];
        // m[1] is IP address, m[2] is hostname
        var regex = /(?:\b|\/)(?:((?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\/[0-9]{1,2})?)|((?:(?:[a-zA-Z0-9]|[a-zA-Z0-9][\u200ba-zA-Z0-9\-]*[a-zA-Z0-9])\u200b?\.\u200b?)+(?:[A-Za-z]|[A-Za-z][\u200bA-Za-z0-9\-]*[A-Za-z0-9])))(?:\b|\/|\u200b)/g;

        var xpathResult = document.evaluate(
            ".//text()[not(ancestor::*[@class='" + ipoo.config.id + "']) and " +
                "not(ancestor::" + notInTags.join(") and not(ancestor::") + ")]",
            container, null, XPathResult.UNORDERED_NODE_SNAPSHOT_TYPE, null
        );

        function lquery(event) {
	    var q = this.alt || this.title;
            chrome.panel.show();
	    chrome.commandline.history.save(q);
            query(q);
	    event.preventDefault();
	    event.stopPropagation();
	    return false;
        }

        /**
         * Turn IP and hostnames contained in a text node to link to IPoo.
         */
        function linkify(node)
        {
            var span = null, link, image;
            var found;
            var i, m, s, p = 0, txt = node.textContent;
            while ((m = regex.exec(txt))) {
                // Do we have an IP address or an hostname? In case of
                // an hostname, we should check against the list of
                // allowed domains.
                if (m[2]) {
                    // We have a hostname. Check if it is authorized.
                    if (ipoo.config.domains) {
                        found = false;
                        for (i = 0; i < ipoo.config.domains.length && !found; i++) {
                            s = m[2].replace(/\u200b/g, '');
                            s = s.substring(s.length - ipoo.config.domains[i].length - 1).toUpperCase();
                            if (s === "." + ipoo.config.domains[i].toUpperCase()) {
                                found = true;
                            }
                        }
                        // No match. The domain name is incorrect.
                        if (!found) {
                            continue;
                        }
                    }
                }

                // We create a span element that will be rebuilt with the
                // text but each occurrence will be replaced by a
                // span.ipoo element with the occurrence and an image who
                // will trigger ipoo on click.
                span = span || document.createElement('span');
                span.appendChild(document.createTextNode(txt.substring(p, m.index)));
                link = document.createElement('span');
                link.setAttribute('class', ipoo.config.id);
                if (!hyperlinks) {
                    link.style.borderBottom = '1px dotted #666';
                    link.appendChild(document.createTextNode(m[0] + '\u00a0'));
                    image = document.createElement('img');
                    image.setAttribute('src', ipoo.config.icon);
                    image.setAttribute('alt', m[0]);
                    image.style.cursor = "help";
                    image.style.verticalAlign = "text-bottom";
		    image.style.border = 0;
                    image.addEventListener("click", lquery, false);
                    link.appendChild(image);
                } else {
                    link.style.borderBottom = '1px solid blue';
                    link.style.color = 'blue';
                    link.style.cursor = "pointer";
                    link.setAttribute('title', m[0]);
                    link.appendChild(document.createTextNode(m[0]));
                    link.addEventListener("click", lquery, false);
                }
                span.appendChild(link);
                p = m.index + m[0].length;
            }
            if (span) {
                // Add the remaining text
		if (p < txt.length) {
                    span.appendChild(document.createTextNode(
			txt.substring(p, txt.length)));
		}
                try {
                    node.parentNode.replaceChild(span, node);
                } catch (e) {
                    fbconsole.error("ipoo: Unable to insert node: " + e.message);
                }
            }
            
        }

        // Process results by batch of 50
        return function () {
            var i = 0;
            return function continuation() {
                var node, limit = 0;
                while ((node = xpathResult.snapshotItem(i++))) {
                    linkify(node);
                    if (++limit > 50) {
                        setTimeout(continuation, 0);
                        return container;
                    }
                }
                return container;
            }();
        }();
    };

    /******************************************************
     * Chrome related functions (purely panel functions)
     */

    /**
     * Namespace for chrome
     */
    chrome = function () {

        var chrome = {};        // Future chrome namespace
        var iframe = null;      // iframe object
        var idoc = null;        // shortcut to iframe.contentWindow.document
        var mini = null;        // mini chrome
        var panel = null;       // panel
        var cmdline = null;     // command line

        /**
         * Function that will create IPoo "chrome window". This is
         * actually an iframe in which the skin is injected.
         */
        chrome.init = function ()
        {
            // Create an iframe and put the appropriate content in it
            iframe = document.createElement("iframe");
            iframe.setAttribute('frameBorder', 0);
            iframe.setAttribute('class', ipoo.config.id);
            iframe.style.border = 0;
            iframe.style.zIndex = "2147483647";
            iframe.style.position = "fixed";
            iframe.style.bottom = "0";
            iframe.style.display = "none";
            iframe.style.visibility = "hidden";
            iframe.addEventListener("load", function () {
                var called = false;
                return function () {
                    if (called) {
                        return;
                    }
                    called = true;
                    getText(ipoo.config.skin, function (html) {
                        // We retrieve the HTML content and put it into the iframe
			if (iframe.contentWindow) {
			    idoc = iframe.contentWindow.document;
			} else { // Google Chrome
			    idoc = iframe.contentDocument;
			}
                        idoc.open();
                        // We alter the CSS to point to the appropriate ressources
                        idoc.write(html.replace(/\burl\(/g,
                                                "url(" + ipoo.config.ws + "static/"));
                        idoc.close();
                        
                        // Window is created. Link various events to appropriate functions
                        mini = idoc.getElementById("ipooMiniChrome");
                        mini.addEventListener("click",
                                              function () {
                                                  chrome.panel.show();
                                              }, false);
                        
                        panel = idoc.getElementById("ipooChrome");
                        idoc.getElementById("ipooButtonMinimize")
                            .addEventListener("click",
                                             function () {
                                                 chrome.mini.show();
                                             }, false);
                        idoc.getElementById("ipooButtonUpDown")
                            .addEventListener("click",
                                             function () {
                                                 chrome.panel.toggle();
                                             }, false);

                        cmdline = idoc.getElementById("ipooCommandLine");
                        cmdline.addEventListener("keydown",
                                                 function (e) {
                                                     chrome.commandline.keypress(e);
                                                 }, true);
                        
                        // We display mini chrome
                        chrome.mini.show();
                        
                        fbconsole.info("ipoo: Chrome is ready");
                    }, function (reason) {
                        fbconsole.alert("unable to get panel content:" + reason);
                    });
                    return false;
                };
            }(), false);
            iframe.setAttribute('src', 'about:blank');
            document.body.appendChild(iframe);
        };

        /**
         * Helper to redraw chrome more efficiently. It takes a
         * function that will be decorated to be more efficient.
         */
        var redraw = function (decorated)
        {
            iframe.style.display = "none";
            iframe.style.visibility = "hidden";
            decorated();
            iframe.style.display = "block";
            iframe.style.visibility = "visible";
        };

        chrome.mini = {
            /**
             * Function to display minichrome on the screen (and hide
             * chrome)
             */
            show: function ()
            {
                redraw(function () {
                    iframe.style.height = "27px";
                    iframe.style.width = "27px";
                    iframe.style.left = "";
                    iframe.style.right = "0";
                    iframe.style.top = "";
                    iframe.style.bottom = "0";
                    mini.style.display = "block";
                    panel.style.display = "none";
                });
            }
        };

        chrome.panel = {
            /**
             * Function to display panel on the screen (and hide
             * chrome)
             */
            show: function ()
            {
                redraw(function () {
                    iframe.style.height = ipoo.config.height + "px";
                    iframe.style.width = "100%";
                    iframe.style.left = "0";
                    iframe.style.right = "";
                    mini.style.display = "none";
                    panel.style.display = "table";
                });
                cmdline.focus();
            },

            /** 
             * Function to toggle panel location
             */
            toggle: function () {
                var atBottom = true;
                return function () {
                    redraw(function () {
                        if (atBottom) {
                            iframe.style.bottom = "";
                            iframe.style.top = "0";
                            atBottom = false;
                        } else {
                            iframe.style.top = "";
                            iframe.style.bottom = "0";
                            atBottom = true;
                        }
                    });
                    cmdline.focus();
                };
            }(),

            /**
             * Function to create a new sub panel. We compute the size
             * of this new subpanel to arrange at most 4 panels in the
             * area. When the area is filled, older panels are removed.
             */
            subpanel: function () {
                var panels = [];

                /* Subpanel object */
                function sub(element) {
                    var loading = null;

                    function append(node, className, text) {
                        var el;
                        el = idoc.createElement(node);
                        if (className) {
                            el.setAttribute("class", className);
                        }
                        el.appendChild(idoc.createTextNode(text));
                        element.insertBefore(el, loading);
                        return el;
                    }

                    return {
                        title: function (text) {
                            append("h1", ipoo.config.id, text);
                        },
                        loading: function () {
                            if (loading) {
                                return;
                            }
                            loading = append("span", "working", "\u00a0");
                        },
                        complete: function () {
                            if (!loading) {
                                return;
                            }
                            element.removeChild(loading);
                        },
                        error: function (message) {
                            append("p", "error", message);
                        },
                        info: function (message) {
                            append("p", "info", message);
                        },
                        section: function (name) {
                            append("h2", null, name + ":\u200b");
                        },
                        pretty: function (data) {
                            // We have an arbitrary object and we need
                            // to build a DOM tree out of it.
                            var empty = function() {
                                var empty = idoc.createElement("span");
                                empty.setAttribute("class", "empty");
                                empty.setAttribute("title", "No result");
                                empty.appendChild(idoc.createTextNode("\u00a0"));
                                return empty;
                            };
                            function pretty(data) {
                                var i, ul, li, tr;
                                if (typeof data === 'object') {
                                    if (data) {
                                        if (data instanceof Array) {
                                            /* Array */
                                            if (!data.length) {
                                                return empty();
                                            }
                                            if (data.length === 1) {
                                                return pretty(data[0]);
                                            }
                                            ul = idoc.createElement("ul");
                                            for (i = 0; i < data.length; i++) {
                                                li = idoc.createElement("li");
                                                li.appendChild(pretty(data[i]));
                                                ul.appendChild(li);
                                            }
                                            return ul;
                                        }
                                        /* object */
                                        li = null;
                                        ul = idoc.createElement("table");
                                        for (i in data) {
                                            if (typeof data[i] !== 'function') {
                                                tr = idoc.createElement("tr");
                                                li = idoc.createElement("td");
                                                li.appendChild(idoc.createTextNode(i));
                                                tr.appendChild(li);
                                                li = idoc.createElement("td");
                                                li.appendChild(pretty(data[i]));
                                                tr.appendChild(li);
                                                ul.appendChild(tr);
                                            }
                                        }
                                        return (li ? ul : empty());
                                    }
                                }
                                if (typeof data === 'string' ||
                                    typeof data === 'number') {
                                    return idoc.createTextNode(data+" ");
                                }
                                /* null, undefined */
                                return empty();
                            }
                            element.insertBefore(pretty(data), loading);
                            setTimeout(function() {
                                linkify(element, idoc, true);
                            }, 0);
                        }
                    };
                }

                return function () {
                    var area = idoc.getElementById("ipooDisplayArea");
                    var p = idoc.createElement("div");
                    p.setAttribute("class", "ipooSubPanel");
                    p.style.height = ipoo.config.height - 36 + "px";
                    p.style.width = ipoo.config.width;
                    p.style.marginLeft = p.style.marginRight = "2px";
                    area.insertBefore(p, panels[panels.length - 1] || null);
                    panels.push(p);
                    if (panels.length*p.offsetWidth > area.offsetWidth - 20) {
                        area.removeChild(panels.shift());
                    }
                    return sub(p);
                };
            }()
        };

        chrome.commandline = function() {
	    var commandline = {};
	    /* Function to handle history. */
	    commandline.history = function() {
		var history = [];
		var position = -1;
		return {
		    save: function(value) {
			value = value || cmdline.value;
			position = history.length;
                        history[position++] = value;
		    },
		    prev: function() {
                        if (position > 0) {
                            cmdline.value = history[--position];
                        }
		    },
		    next: function() {
                        if (position < history.length - 1) {
                            cmdline.value = history[++position];
                        } else if (position === history.length - 1) {
                            position++;
                            cmdline.value = "";
                        }
		    }
		};
	    }();

            /**
             * Function to handle a keypress in the command line. This
             * function should be called with the event that triggered
             * it.
             */
            commandline.keypress = function () {
                return function (event) {
                    var code = event.keyCode;
                    if (code === 13 /* enter */) {
                        if (cmdline.value) {
			    commandline.history.save();
                            query(cmdline.value);
                        }
                        cmdline.value = "";
                    } else if (code === 27 /* esc */) {
                        cmdline.value = "";
                    } else if (code === 38 /* up */) {
			commandline.history.prev();
                    } else if (code === 40 /* down */) {
			commandline.history.next();
                    } else {
                        return;
                    }
                    event.preventDefault();
                    return false;
                };
            }();

	    return commandline;
        }();

        return chrome;
    }();

    /******************************************************
     * Public functions
     */

    /**
     * Setup IPoo for the current document.
     * This means:
     *    - grab configuration from web service
     *    - linkify the document
     *    - watch for new DOM object
     *    - build the panel
     *
     * This function can be called while the document is not ready yet.
     */
    ipoo.setup = function ()
    {
        // We need both domains and DOM to be able to build the interface
        var isDomReady = ipoo.config.greasemonkey;
        var hasDomains = false;
        var called = false;
        if ('text/xml' === document.contentType ||
            'application/xml' === document.contentType ||
            'text/plain' === document.contentType) {
            return;
        }

        // Helper that effectively prepare the document and build the interface
        function prepare()
        {
            // Should be called once
            if (called) {
                return;
            }
            called = true;
            chrome.init();
            linkify(document, document);
	    document.body.addEventListener('DOMNodeInserted',
                                           function (event) {
					       linkify(event.target, document);
                                           }, false);
        }
        // Helper called when we got domains.
        function gotDomains(domains)
        {
            // Assign domains to configuration
            ipoo.config.domains = domains.domains;
            hasDomains = true;
            if (ipoo.config.domains !== undefined) {
                fbconsole.info("ipoo: Received supported domains");
            }
            if (isDomReady) {
                prepare();
            }
        }
        // Helper called when DOM is ready
        function domReady()
        {
            isDomReady = true;
            fbconsole.info("ipoo: DOM is ready");
            if (hasDomains) {
                prepare();
            }
            return false;
        }

        // Tell us when DOM is ready
        document.addEventListener("DOMContentLoaded",
                                  domReady,
                                  false);
        // We want to get domains. If we are not able to get them, we
        // work with an empty list.
        fbconsole.info("ipoo: grab list of supported domains from server");
        getJSON("api/1.0/cfg/", gotDomains, function (reason) {
            fbconsole.warn("ipoo: unable to retrieve supported domains: " + reason);
            gotDomains(undefined);
        });
    };

    return ipoo;
}();
