baseURL = "https://example.com/nms/api/v2.1/"
xAuthToken = ""
# These should be the networks your customers are assigned to
validNetworks = [IPv4Network('100.64.0.0/10'),IPv4Network('1.1.1.0/24')]
# These should be the addresses of any devices within the validNetworks ranges that should NEVER be suspended (i.e. your actual infrastructure router IPs 
notAllowed = [IPv4Address('100.64.0.1'),IPv4Address('1.1.1.1')]
# Edge router here is the router performing suspension, ideally at the edge of your network
edgeRouterIP = "100.129.0.1"
edgeRouterUser = "suspension"
edgeRouterPassword = ""
