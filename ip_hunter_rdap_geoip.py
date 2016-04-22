#!/usr/bin/python
'''
Python 3.5 compatible
This will create a comma delimited file
it requires you to have a GeoIP2-City database from MaxMind.
  https://www.maxmind.com/en/geoip2-databases
  https://www.maxmind.com/en/geolite2-developer-package

If you do not wish to purchase this, consider using the shodan package instead as you can pull geo data from there as well

Dependency on 
1) geoip2
2) ipwhois
'''
import csv
import datetime
import geoip2.database
import os.path
import sys
from ipwhois import IPWhois

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def newline_clean(original):
    try:
        cleaned = original.replace("\n","|").replace("\r","|").replace("\t","|")
    except:
         cleaned = original#shame on me for this
    return cleaned

def getMaxMind(ip_address):
    ip_addy = ip_address
    geo_ip = {"MaxMind_ip_iso_code":"UNK","MaxMind_ip_country":"UNK","MaxMind_ip_state":"UNK","MaxMind_ip_city":"UNK","MaxMind_ip_zipcode":"UNK"}
    #open GeoIP2 data reader
    reader = geoip2.database.Reader("/path/to/Maxmind/GeoIP2-City.mmdb")
    try:
        ip = reader.city(ip_addy)
        geo_ip["MaxMind_ip_iso_code"] = (newline_clean(ip.country.iso_code)) #US
        geo_ip["MaxMind_ip_country"] = (newline_clean(ip.country.name)) #'United States'
        geo_ip["MaxMind_ip_state"] = (newline_clean(ip.subdivisions.most_specific.name)) #'Minnesota'
        geo_ip["MaxMind_ip_city"] = (newline_clean(ip.city.name)) #'Minneapolis'
        geo_ip["MaxMind_ip_zipcode"] = (newline_clean(ip.postal.code)) #'55455'
    except:
        print("Unexpected Error getting MaxMind GeoIP data for: "+ip_addy)
    reader.close()
    return geo_ip

dt = datetime.date.today()
input_path = "/path/to/myinput/"
input_name = "$inputfilename.txt"
input_file_name = os.path.join(input_path, input_name)
output_path = "/path/to/myoutput/"
output_name = ("IP_details_"+str(dt)+".csv")
output_file_name = os.path.join(output_path, output_name)
process_file_name = os.path.join(input_path,"cleaned_input.txt")
errors_file = os.path.join(output_path,"processing errors.txt")

#sort file and stripout blank lines
with open(input_file_name,"r") as f, open(process_file_name,"w")as f2:
    seen = set()
    for line in f:
        line.strip(" \n\t\r abcdefghijklmnopqrstuvwxyz")
        if line in seen: continue
        f2.write(line)
        seen.add(line)

work = file_len(process_file_name)
print(str(work)+" ips to process\n")

with open(process_file_name,"r") as fin, open(output_file_name,"w",newline='',encoding="ascii", errors="ignore") as csvfile:

    #set up CSV file
    fieldnames = ["ip_addr" , "handle" , "asn" , "asn_country_code" , "network_cidr" , "contact_address" , "contact_email" , "contact_phone" , "contact_name" , "contact_title" , "contact_role" , "MaxMind_ip_iso_code" , "MaxMind_ip_country" , "MaxMind_ip_state" , "MaxMind_ip_city" , "MaxMind_ip_zipcode"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    #set up variables
    addr = "UNK"
    handle = "UNK"
    asn = "UNK"
    asn_country_code = "UNK"
    network_cidr = "UNK"
    contact_address = "UNK"
    contact_email = "UNK"
    contact_phone = "UNK"
    contact_name = "UNK"
    contact_title = "UNK"
    contact_role = "UNK"
    
    for line in fin:
        addr = line.rstrip().strip()
        print("Processing "+str(addr)+" "+str(work)+" more IP's to go")

        #Get GeoIP data from MaxMind database
        geo_data = getMaxMind(addr)#returns a dictionary
        MaxMind_ip_iso_code = geo_data.pop("MaxMind_ip_iso_code")
        MaxMind_ip_country = geo_data.pop("MaxMind_ip_country")
        MaxMind_ip_state = geo_data.pop("MaxMind_ip_state")
        MaxMind_ip_city = geo_data.pop("MaxMind_ip_city")
        MaxMind_ip_zipcode = geo_data.pop("MaxMind_ip_zipcode")
        geo_data.clear() #for good measure

        #Get WhoIs Data
        try:
            obj = IPWhois(addr, timeout=20)
            results = obj.lookup_rdap(depth=1)
            asn = (newline_clean(results['asn']))
            asn_country_code = (newline_clean(results['asn_country_code']))
            network_cidr = (newline_clean(results['network']['cidr']))
            #Entry identifier - this is the Internet Registry Number, known as the handle Ex:ZG39-ARIN for Google
            for object_key, object_dict in results['objects'].items():
                handle = str(object_key)
                handle = (handle)
                if results['objects'] is not None:
                    for k in results['objects']:
                        #Address - first result only
                        tmp_add = results['objects'][k]['contact']['address']
                        if tmp_add is not None:
                            contact_address = (newline_clean(tmp_add[0]['value']))

                        #Email - first result only
                        tmp_em = results['objects'][k]['contact']['email']
                        if tmp_em is not None:
                            contact_email = (newline_clean(tmp_em[0]['value']))

                        #Phone - first result only
                        tmp_ph = results['objects'][k]['contact']['phone']
                        if tmp_ph is not None:
                            contact_phone = (newline_clean(tmp_ph[0]['value']))

                        #Name - string result
                        tmp_nm = results['objects'][k]['contact']['name']
                        if tmp_nm is not None:
                            contact_name = (newline_clean(tmp_nm))

                        #Title - string result
                        tmp_ti = results['objects'][k]['contact']['title']
                        if tmp_ti is not None:
                            contact_title = (newline_clean(tmp_ti))

                        #Role - string result
                        tmp_ro = results['objects'][k]['contact']['role']
                        if tmp_ro is not None:
                            contact_role = (newline_clean(tmp_ro))

            #Create Entry
            writer.writerow({"ip_addr" : addr,
                             "handle" : handle,
                             "asn" : asn,
                             "asn_country_code" : asn_country_code,
                             "network_cidr" : network_cidr,
                             "contact_address" : contact_address,
                             "contact_email" : contact_email,
                             "contact_phone" : contact_phone,
                             "contact_name" : contact_name,
                             "contact_title" : contact_title,
                             "contact_role" : contact_role,
                             "MaxMind_ip_iso_code" : MaxMind_ip_iso_code,
                             "MaxMind_ip_country" : MaxMind_ip_country,
                             "MaxMind_ip_state" : MaxMind_ip_state,
                             "MaxMind_ip_city" : MaxMind_ip_city,
                             "MaxMind_ip_zipcode": MaxMind_ip_zipcode})

        except Exception as e:
            #FWIW, there's much better ways to log errors, but I don't need it for what I am doing
            with open(errors_file,"a") as ferr:
                ferr.write("Unexpected error getting WhoIs info for: "+addr)
                ferr.write("\n")

        work = work-1

print("done")
