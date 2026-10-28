"""README showcase diagrams for aws-diagram-design, built with the bundled generator.

    bash docs/samples/build_samples.sh        # → docs/samples/<slug>.svg + .png

Four AWS architecture diagrams in the compact house layout: box widths from min_node_w, 56 px boxes
with 24 px official icons, neighbours 40 px apart (label-mask + 16 px when the connector is labelled),
rows 40 px apart, 24 px zone padding, one focal node each, arrow labels in the sublabel face.
English only; `lang` is ignored.
"""
from awsdiag import Canvas, min_node_w, text_w, LABEL_SIZE

H, ROW, PAD = 56, 40, 24
up4 = lambda v: int(-(-v // 4) * 4)
gap = lambda label=None: 40 if not label else up4(text_w(label, LABEL_SIZE) + 24)
W = lambda name, sub: up4(min_node_w(name, sub, True, H))


def serverless():
    w_u, w_cf, w_api, w_l = W("Users", "web / mobile"), W("CloudFront", "CDN edge"), W("API Gateway", "REST /api"), W("Lambda", "node.js 22")
    w_cf = max(w_cf, W("Amazon S3", "static assets")); w_l = max(w_l, W("DynamoDB", "orders table"))
    x_u = 40; x_cf = x_u + w_u + gap("HTTPS"); x_api = x_cf + w_cf + gap("DYNAMIC"); x_l = x_api + w_api + gap("INVOKE")
    zx, zw = x_cf - PAD, (x_l + w_l + PAD) - (x_cf - PAD)
    y1 = 80; y2 = y1 + H + ROW; zh = y2 + H + PAD - 40
    c = Canvas(up4(zx + zw + 40), up4(zh + 80), "serverless-web-app", "Serverless Web Application",
               "Users reach CloudFront, which serves static assets from S3 and routes dynamic requests through API Gateway to a Lambda function backed by DynamoDB.")
    c.zone(zx, 40, zw, zh, "AWS Cloud", kind="cloud")
    cy = y1 + H // 2
    c.path(c.hline(x_u + w_u, cy, x_cf), style="link"); c.label((x_u + w_u + x_cf) / 2, cy - 12, "HTTPS", color="#0972D3")
    c.path(c.hline(x_cf + w_cf, cy, x_api)); c.label((x_cf + w_cf + x_api) / 2, cy - 12, "DYNAMIC")
    c.path(c.hline(x_api + w_api, cy, x_l), style="accent"); c.label((x_api + w_api + x_l) / 2, cy - 12, "INVOKE", color="#EC7211")
    for x, w, lab in ((x_cf, w_cf, "STATIC"), (x_l, w_l, "QUERY")):
        cx = x + w // 2; c.path(c.vline(cx, y1 + H, y2)); c.label(cx + 12, y1 + H + ROW // 2 + 5, lab, anchor="start")
    c.node(x_u, y1, w_u, H, "Users", "web / mobile", icon="Users", kind="input")
    c.node(x_cf, y1, w_cf, H, "CloudFront", "CDN edge", icon="CloudFront")
    c.node(x_api, y1, w_api, H, "API Gateway", "REST /api", icon="APIGateway")
    c.node(x_l, y1, w_l, H, "Lambda", "node.js 22", icon="Lambda", kind="focal")
    c.node(x_cf, y2, w_cf, H, "Amazon S3", "static assets", icon="S3", kind="store")
    c.node(x_l, y2, w_l, H, "DynamoDB", "orders table", icon="DynamoDB", kind="store")
    return c


def vpc_three_tier():
    w_u, w_alb, w_ecs = W("Users", "internet"), W("ALB", "HTTPS :443"), W("ECS on Fargate", "app service")
    w_db = max(W("Amazon RDS", "postgres multi-az"), W("ElastiCache", "redis cache"))
    x_u = 40
    cx0 = x_u + w_u + PAD                       # cloud left edge; three nested borders then the ALB
    vx0 = cx0 + PAD; px0 = vx0 + PAD; x_alb = px0 + PAD
    sub_gap = lambda label: max(gap(label), 3 * PAD - PAD + 16)     # two subnet borders + 16 px air between subnets
    x_ecs = x_alb + w_alb + sub_gap("FORWARD"); x_db = x_ecs + w_ecs + sub_gap("SQL")
    y_cloud, y_vpc, y_sub = 40, 80, 120; y1 = y_sub + 40; y2 = y1 + H + ROW
    sub_h = y2 + H + PAD - y_sub; vpc_h = sub_h + 40 + PAD; cloud_h = vpc_h + 40 + PAD
    sw = lambda w: w + 2 * PAD
    data_right = x_db + w_db + PAD; vpc_right = data_right + PAD; cloud_right = vpc_right + PAD
    c = Canvas(up4(cloud_right + 40), up4(y_cloud + cloud_h + 40), "vpc-three-tier", "VPC Three-Tier Web Service",
               "Internet users reach an Application Load Balancer in a public subnet, which forwards to an ECS on Fargate service in a private subnet backed by RDS and an ElastiCache cache in a private data subnet.")
    c.zone(cx0, y_cloud, cloud_right - cx0, cloud_h, "AWS Cloud", kind="cloud")
    c.zone(vx0, y_vpc, vpc_right - vx0, vpc_h, "VPC · 10.0.0.0/16", kind="vpc")
    c.zone(px0, y_sub, sw(w_alb), sub_h, "Public subnet", kind="public")
    c.zone(x_ecs - PAD, y_sub, sw(w_ecs), sub_h, "Private subnet", kind="private")
    c.zone(x_db - PAD, y_sub, sw(w_db), sub_h, "Private subnet", kind="private")
    cy = y1 + H // 2
    c.path(c.hline(x_u + w_u, cy, x_alb), style="link"); c.label((x_u + w_u + x_alb) / 2, cy - 12, "HTTPS", color="#0972D3")
    c.path(c.hline(x_alb + w_alb, cy, x_ecs)); c.label((x_alb + w_alb + x_ecs) / 2, cy - 12, "FORWARD")
    c.path(c.hline(x_ecs + w_ecs, cy, x_db)); c.label((x_ecs + w_ecs + x_db) / 2, cy - 12, "SQL")
    ecs_cx = x_ecs + w_ecs // 2
    c.path(c.L_vh(ecs_cx, y1 + H, x_db, y2 + H // 2), dashed=True); c.label(ecs_cx + 12, y1 + H + ROW // 2 + 5, "CACHE", anchor="start")
    c.node(x_u, y1, w_u, H, "Users", "internet", icon="Users", kind="input")
    c.node(x_alb, y1, w_alb, H, "ALB", "HTTPS :443", icon="ALB")
    c.node(x_ecs, y1, w_ecs, H, "ECS on Fargate", "app service", icon="Fargate", kind="focal")
    c.node(x_db, y1, w_db, H, "Amazon RDS", "postgres multi-az", icon="RDS", kind="store")
    c.node(x_db, y2, w_db, H, "ElastiCache", "redis cache", icon="ElastiCache", kind="store")
    return c


def event_driven():
    w_p, w_k = W("Producers", "apps · devices"), W("Kinesis Streams", "data stream")
    w_l = max(W("Lambda", "transform"), W("Athena", "SQL query")); w_s3 = max(W("S3 Data Lake", "parquet"), W("Glue Catalog", "crawler · schema"))
    x_p = 40; x_k = x_p + w_p + gap("EVENTS"); x_l = x_k + w_k + gap("STREAM"); x_s3 = x_l + w_l + gap("WRITE")
    zx, zw = x_k - PAD, (x_s3 + w_s3 + PAD) - (x_k - PAD)
    y1 = 80; y2 = y1 + H + ROW; zh = y2 + H + PAD - 40
    c = Canvas(up4(zx + zw + 40), up4(zh + 80), "event-driven-pipeline", "Event-Driven Data Pipeline",
               "Producers stream events into Kinesis, a Lambda function transforms them into an S3 data lake, and Glue catalogs the data so Athena can query it in place.")
    c.zone(zx, 40, zw, zh, "AWS Cloud", kind="cloud")
    cy = y1 + H // 2
    c.path(c.hline(x_p + w_p, cy, x_k), style="link"); c.label((x_p + w_p + x_k) / 2, cy - 12, "EVENTS", color="#0972D3")
    c.path(c.hline(x_k + w_k, cy, x_l)); c.label((x_k + w_k + x_l) / 2, cy - 12, "STREAM")
    c.path(c.hline(x_l + w_l, y1 + H // 3, x_s3), style="accent"); c.label((x_l + w_l + x_s3) / 2, y1 + H // 3 - 12, "WRITE", color="#EC7211")
    s3_cx = x_s3 + w_s3 // 2
    c.path(c.vline(s3_cx, y1 + H, y2)); c.label(s3_cx + 12, y1 + H + ROW // 2 + 5, "CRAWL", anchor="start")
    c.path(c.hline(x_s3, y2 + 3 * H // 4, x_l + w_l)); c.label((x_l + w_l + x_s3) / 2, y2 + 3 * H // 4 + 22, "SCHEMA")
    scan_mid = x_s3 - PAD
    c.path(c.elbow_hvh(x_l + w_l, y2 + H // 4, x_s3, y1 + 2 * H // 3, mid=scan_mid), style="link", dashed=True)
    c.label(scan_mid - 12, y1 + H + ROW // 2 + 5, "SCAN", anchor="end", color="#0972D3")
    c.node(x_p, y1, w_p, H, "Producers", "apps · devices", icon="cloud", kind="input")
    c.node(x_k, y1, w_k, H, "Kinesis Streams", "data stream", icon="Amazon-Kinesis-Data-Streams")
    c.node(x_l, y1, w_l, H, "Lambda", "transform", icon="Lambda")
    c.node(x_s3, y1, w_s3, H, "S3 Data Lake", "parquet", icon="S3", kind="focal")
    c.node(x_l, y2, w_l, H, "Athena", "SQL query", icon="Athena")
    c.node(x_s3, y2, w_s3, H, "Glue Catalog", "crawler · schema", icon="Glue")
    return c


def multi_region():
    w_app = max(W("App A", "web tier"), W("App B", "web tier")); w_tgw = max(W("Transit Gateway", "tgw · use1"), W("Transit Gateway", "tgw · apne2"))
    w_wan, w_dx, w_srv = W("AWS Cloud WAN", "core network · global"), W("Direct Connect", "dx gateway"), W("Servers", "10.9.0.0/16")
    g_attach = max(gap("ATTACH"), 3 * PAD + 24)             # vpc + account + account borders, 24 px air between accounts
    # vertical structure: cloud → region → account → vpc → app
    y_cloud, y_reg, y_acc, y_vpc = 40, 80, 120, 160; y_app = y_vpc + 40
    vpc_h = 40 + H + PAD; acc_h = vpc_h + 40 + PAD; reg_h = acc_h + 40 + PAD
    y_tgw = y_app                                             # TGW on the App row: ATTACH is a straight 96 px run
    y_wan = y_reg + reg_h + 48; peer_mid = y_reg + reg_h + 16
    cloud_h = y_wan + H + PAD - y_cloud
    y_prem = y_cloud + cloud_h + 40; y_srv = y_prem + 40; prem_h = 40 + H + PAD
    # horizontal structure, left → right
    x_cloud = 40; x_reg1 = x_cloud + PAD; x_accA = x_reg1 + PAD; x_vpcA = x_accA + PAD; x_appA = x_vpcA + PAD
    vpc_w = w_app + 2 * PAD; acc_w_work = vpc_w + 2 * PAD; acc_w_net = w_tgw + 2 * PAD
    x_tgw1 = x_appA + w_app + g_attach; x_accN1 = x_tgw1 - PAD
    reg1_right = x_accN1 + acc_w_net + PAD; reg_w = reg1_right - x_reg1
    x_reg2 = reg1_right + PAD; x_accN2 = x_reg2 + PAD; x_tgw2 = x_accN2 + PAD
    x_appB = x_tgw2 + w_tgw + g_attach; x_vpcB = x_appB - PAD; x_accB = x_vpcB - PAD
    cloud_right = x_reg2 + reg_w + PAD
    tgw1_cx, tgw2_cx = x_tgw1 + w_tgw // 2, x_tgw2 + w_tgw // 2
    x_wan = (tgw1_cx + tgw2_cx) // 2 - w_wan // 2; x_wan -= x_wan % 4
    x_dx = x_wan - gap("BGP") - w_dx
    x_srv = x_dx + (w_dx - w_srv) // 2; x_srv -= x_srv % 4; x_prem = x_srv - PAD
    c = Canvas(up4(cloud_right + 40), up4(y_prem + prem_h + 40), "multi-region-network", "Multi-Region Network Backbone",
               "Workload VPCs in us-east-1 and ap-northeast-2 attach to per-region Transit Gateways in network accounts, the gateways peer into an AWS Cloud WAN core network, and an on-premises data center connects over Direct Connect with a VPN backup path.")
    c.zone(x_cloud, y_cloud, cloud_right - x_cloud, cloud_h, "AWS Cloud", kind="cloud")
    c.zone(x_reg1, y_reg, reg_w, reg_h, "us-east-1", kind="region"); c.zone(x_reg2, y_reg, reg_w, reg_h, "ap-northeast-2", kind="region")
    c.zone(x_accA, y_acc, acc_w_work, acc_h, "Workload account A", kind="account"); c.zone(x_accN1, y_acc, acc_w_net, acc_h, "Network account", kind="account")
    c.zone(x_accN2, y_acc, acc_w_net, acc_h, "Network account", kind="account"); c.zone(x_accB, y_acc, acc_w_work, acc_h, "Workload account B", kind="account")
    c.zone(x_vpcA, y_vpc, vpc_w, vpc_h, "VPC 10.1.0.0/16", kind="vpc"); c.zone(x_vpcB, y_vpc, vpc_w, vpc_h, "VPC 10.2.0.0/16", kind="vpc")
    c.zone(x_prem, y_prem, w_srv + 2 * PAD, prem_h, "On-premises", kind="corporate")
    # connectors
    app_cy, tgw_cy = y_app + H // 2, y_tgw + H // 2
    c.path(c.hline(x_appA + w_app, app_cy, x_tgw1)); c.label(x_appA + w_app + g_attach // 2, app_cy - 12, "ATTACH")   # mask may cover zone borders (zones paint first)
    c.path(c.hline(x_appB, app_cy, x_tgw2 + w_tgw)); c.label(x_appB - g_attach // 2, app_cy - 12, "ATTACH")
    for cx, tx in ((tgw1_cx, x_wan + w_wan // 4), (tgw2_cx, x_wan + 3 * w_wan // 4)):
        c.path(c.elbow_vhv(cx, y_tgw + H, tx, y_wan, mid=peer_mid)); c.label((cx + tx) / 2, peer_mid + 22, "PEERING")
    wan_cy = y_wan + H // 2
    c.path(c.hline(x_dx + w_dx, wan_cy, x_wan), style="link"); c.label((x_dx + w_dx + x_wan) / 2, wan_cy - 12, "BGP", color="#0972D3")
    srv_cx = x_srv + w_srv // 2
    c.path(c.vline(srv_cx, y_srv, y_wan + H), style="link")                     # Servers → Direct Connect (DX sits right above)
    wan_cx = x_wan + w_wan // 2
    c.path(c.L_hv(x_srv + w_srv, y_srv + H // 2, wan_cx, y_wan + H), style="link", dashed=True)
    c.label((x_srv + w_srv + wan_cx) / 2, y_srv + H // 2 - 12, "VPN BACKUP", color="#0972D3")
    # nodes
    c.node(x_appA, y_app, w_app, H, "App A", "web tier", icon="EC2Instance"); c.node(x_appB, y_app, w_app, H, "App B", "web tier", icon="EC2Instance")
    c.node(x_tgw1, y_tgw, w_tgw, H, "Transit Gateway", "tgw · use1", icon="AWS-Transit-Gateway"); c.node(x_tgw2, y_tgw, w_tgw, H, "Transit Gateway", "tgw · apne2", icon="AWS-Transit-Gateway")
    c.node(x_wan, y_wan, w_wan, H, "AWS Cloud WAN", "core network · global", icon="AWS-Cloud-WAN", kind="focal")
    c.node(x_dx, y_wan, w_dx, H, "Direct Connect", "dx gateway", icon="AWS-Direct-Connect")
    c.node(x_srv, y_srv, w_srv, H, "Servers", "10.9.0.0/16", icon="Server", kind="external")
    return c


def build(lang):
    return [(c.slug, c) for c in (serverless(), vpc_three_tier(), event_driven(), multi_region())]
