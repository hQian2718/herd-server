# herd-server
In this final project for my Programming Languages class at UCLA, I am placed in the context of building a Wikimedia-style service designed for news, where 
(1) updates to articles will happen far more often, 
(2) access will be required via various protocols, not just HTTP or HTTPS, and 
(3) clients will tend to be more mobile. 

However, in this service the PHP+JavaScript application server in Wikimedia Foundation's architecture looks like it will be a bottleneck. It is difficult to add newer servers (e.g., for access via cell phones, where the cell phones are frequently broadcasting their GPS locations), and the response time looks like it will too slow because the Wikimedia application server is a central bottleneck on the core clusters.

I examined another architecutre called the "application server herd", where the multiple application servers communicate directly to each other as well as via the core database and caches. The interserver communications are designed for rapidly-evolving data (ranging from small stuff such as GPS-based locations to larger stuff such as ephemeral video data) whereas the database server will still be used for more-stable data that is less-often accessed or that requires transactional semantics. 

If a user's cell phone posts its GPS location to any one of the application servers,that server will communicate with its neighbors, and the other servers will learn of the location after one or two interserver transmissions, without having to talk to the database.

The bulk of the project comes down to investigating Python's asyncio asynchronous networking library as a candidate. I conducted research on this library and python
in general, investigating the ease of use, flexibility, reliability of writing servers
with this language. I also looked into how easy it is to integrate this technology 
with other software, and other candidates for this problem.

From a language perspective, my report addresses Python's implementation of type checking, memory management, and multithreading, particularly as the application scales up. As a demo and part of the research process, I wrote a python client-server prototype for communicating client locations through Google Places.

