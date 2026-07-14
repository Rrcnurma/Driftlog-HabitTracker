"""
network_setup.py
File ini isinya fungsi-fungsi buat menyiapkan jaringan cloud (VPC, Subnet, dll)
sebelum EC2 instance (web server) dinyalakan.

Urutan yang dijalankan (sesuai requirement tugas):
1. Buat VPC
2. Buat & attach Internet Gateway ke VPC itu
3. Buat Public Subnet di dalam VPC
4. Buat Route Table, kasih route ke Internet Gateway, hubungkan ke subnet
5. Buat Security Group, buka port 80 (HTTP) & 22 (SSH)
"""

from backend.aws_client import get_ec2_client

CIDR_VPC = '10.0.0.0/16'
CIDR_SUBNET = '10.0.1.0/24'


def buat_vpc():
    """
    Membuat VPC baru.
    Return: vpc_id (string), contoh: 'vpc-abc123'
    """
    ec2 = get_ec2_client()
    response = ec2.create_vpc(CidrBlock=CIDR_VPC)
    vpc_id = response['Vpc']['VpcId']
    print(f"VPC berhasil dibuat: {vpc_id}")
    return vpc_id


def buat_dan_pasang_internet_gateway(vpc_id):
    """
    Membuat Internet Gateway, lalu "memasangnya" (attach) ke VPC.
    Internet Gateway ini yang bikin VPC bisa akses/diakses dari internet.

    Parameter:
        vpc_id: ID dari VPC yang sudah dibuat sebelumnya

    Return: igw_id (string)
    """
    ec2 = get_ec2_client()

    response = ec2.create_internet_gateway()
    igw_id = response['InternetGateway']['InternetGatewayId']

    # Setelah dibuat, IGW masih "lepas", belum terhubung ke VPC manapun.
    # attach_internet_gateway itu yang menghubungkannya.
    ec2.attach_internet_gateway(
        InternetGatewayId=igw_id,
        VpcId=vpc_id
    )

    print(f"Internet Gateway berhasil dibuat & dipasang ke VPC: {igw_id}")
    return igw_id


def buat_public_subnet(vpc_id):
    """
    Membuat subnet publik di dalam VPC.

    Parameter:
        vpc_id: ID dari VPC yang sudah dibuat

    Return: subnet_id (string)
    """
    ec2 = get_ec2_client()

    response = ec2.create_subnet(
        VpcId=vpc_id,
        CidrBlock=CIDR_SUBNET,
        AvailabilityZone='us-east-1'
    )
    subnet_id = response['Subnet']['SubnetId']
    print(f"Public Subnet berhasil dibuat: {subnet_id}")
    return subnet_id


def buat_route_table(vpc_id, igw_id, subnet_id):
    """
    Membuat Route Table, menambahkan rute ke Internet Gateway,
    lalu menghubungkan (associate) Route Table itu ke subnet.

    Ini langkah yang bikin subnet "publik" beneran (subnet baru dianggap
    publik kalau route table-nya punya jalur ke Internet Gateway).

    Parameter:
        vpc_id: ID VPC
        igw_id: ID Internet Gateway
        subnet_id: ID Subnet yang mau dijadikan publik

    Return: route_table_id (string)
    """
    ec2 = get_ec2_client()

    # 1. Buat Route Table baru di dalam VPC
    response = ec2.create_route_table(VpcId=vpc_id)
    route_table_id = response['RouteTable']['RouteTableId']

    # 2. Tambahkan rute: "kalau tujuan alamat manapun (0.0.0.0/0),
    #    lewatkan ke Internet Gateway"
    ec2.create_route(
        RouteTableId=route_table_id,
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw_id
    )

    # 3. Hubungkan Route Table ini ke subnet publik kita
    ec2.associate_route_table(
        RouteTableId=route_table_id,
        SubnetId=subnet_id
    )

    print(f"Route Table berhasil dibuat & dihubungkan ke subnet: {route_table_id}")
    return route_table_id


def buat_security_group(vpc_id):
    """
    Membuat Security Group yang membuka:
    - Port 80 (HTTP)  -> supaya web server bisa diakses lewat browser
    - Port 22 (SSH)   -> supaya bisa diakses/dikelola dari jarak jauh

    Parameter:
        vpc_id: ID VPC

    Return: security_group_id (string)
    """
    ec2 = get_ec2_client()

    response = ec2.create_security_group(
        GroupName='driftlog-web-sg',
        Description='Security group untuk web server Driftlog (HTTP & SSH)',
        VpcId=vpc_id
    )
    sg_id = response['GroupId']

    # authorize_security_group_ingress = "izinkan koneksi MASUK (ingress)"
    # IpPermissions berisi daftar aturan yang mau ditambahkan sekaligus.
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 80,
                'ToPort': 80,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            },
        ]
    )

    print(f"Security Group berhasil dibuat (port 80 & 22 terbuka): {sg_id}")
    return sg_id


def setup_jaringan_lengkap():
    """
    Fungsi "utama" yang menjalankan SEMUA langkah di atas secara berurutan.
    Ini yang nanti dipanggil dari report_engine.py / GUI, cukup satu baris.

    Return: dictionary berisi semua ID yang dihasilkan, contoh:
        {
            "vpc_id": "vpc-xxx",
            "igw_id": "igw-xxx",
            "subnet_id": "subnet-xxx",
            "route_table_id": "rtb-xxx",
            "security_group_id": "sg-xxx"
        }
    """
    print("=== Mulai setup jaringan ===")

    vpc_id = buat_vpc()
    igw_id = buat_dan_pasang_internet_gateway(vpc_id)
    subnet_id = buat_public_subnet(vpc_id)
    route_table_id = buat_route_table(vpc_id, igw_id, subnet_id)
    security_group_id = buat_security_group(vpc_id)

    print("=== Setup jaringan selesai ===")

    return {
        'vpc_id': vpc_id,
        'igw_id': igw_id,
        'subnet_id': subnet_id,
        'route_table_id': route_table_id,
        'security_group_id': security_group_id,
    }