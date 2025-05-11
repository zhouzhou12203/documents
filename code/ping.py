import subprocess
import re
import platform

def ping_domain(domain):
  """Pings a domain and returns the average latency in milliseconds.

  Args:
    domain: The domain to ping.

  Returns:
    The average latency in milliseconds, or None if the ping fails.
  """

  param = '-n' if platform.system().lower()=='windows' else '-c'
  command = ['ping', param, '3', domain] # Ping 3 times for better accuracy

  try:
    result = subprocess.run(command, capture_output=True, text=True, timeout=10) # Increased timeout for slower connections
    output = result.stdout
  except subprocess.TimeoutExpired:
    print(f"Ping timed out for {domain}")
    return None
  except Exception as e:
    print(f"Error pinging {domain}: {e}")
    return None


  if result.returncode != 0:
    print(f"Ping failed for {domain}: {result.stderr}")
    return None


  if platform.system().lower()=='windows':
      # Windows latency extraction - Try Chinese locale first
      match = re.search(r"平均 = (\d+)ms", output)
      if match:
          return int(match.group(1))
      else:
          # If Chinese regex fails, try the English regex
          match = re.search(r"Average = (\d+)ms", output)
          if match:
              return int(match.group(1))
          else:
            #Try alternative pattern if previous ones fail
            match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
            if match:
              return int(match.group(3))
            else:
              #Try alternative pattern if previous ones fail, now in chinese
              match = re.search(r"最短 = (\d+)ms，最长 = (\d+)ms，平均 = (\d+)ms", output)
              if match:
                return int(match.group(3))
              else:
                print(f"Could not extract latency from Windows ping output for {domain}: {output}")
                return None
  else:
      # Linux/macOS latency extraction
      match = re.search(r"rtt min/avg/max/mdev = [\d\.]+/(?P<avg>[\d\.]+)/[\d\.]+/", output)
      if match:
          return float(match.group("avg"))
      else:
          print(f"Could not extract latency from Linux/macOS ping output for {domain}: {output}")
          return None



def find_lowest_latency(domains):
  """Finds the domains with the lowest latency.

  Args:
    domains: A list of domains to ping.

  Returns:
    A list of tuples, where each tuple contains a domain and its latency,
    sorted by latency in ascending order.  Returns None if pinging fails for all domains.
  """

  latencies = []
  for domain in domains:
    latency = ping_domain(domain)
    if latency is not None:
      latencies.append((domain, latency))

  if not latencies:
      print("Failed to ping any of the domains.")
      return None

  latencies.sort(key=lambda x: x[1])
  return latencies

def main():
  """Main function."""

  domains = [
      "objectstorage.ap-sydney-1.oraclecloud.com",
      "objectstorage.ap-melbourne-1.oraclecloud.com",
      "objectstorage.sa-saopaulo-1.oraclecloud.com",
      "objectstorage.sa-vinhedo-1.oraclecloud.com",
      "objectstorage.ca-montreal-1.oraclecloud.com",
      "objectstorage.ca-toronto-1.oraclecloud.com",
      "objectstorage.sa-santiago-1.oraclecloud.com",
      "objectstorage.sa-valparaiso-1.oraclecloud.com",
      "objectstorage.sa-bogota-1.oraclecloud.com",
      "objectstorage.eu-paris-1.oraclecloud.com",
      "objectstorage.eu-marseille-1.oraclecloud.com",
      "objectstorage.eu-frankfurt-1.oraclecloud.com",
      "objectstorage.ap-hyderabad-1.oraclecloud.com",
      "objectstorage.ap-mumbai-1.oraclecloud.com",
      "objectstorage.il-jerusalem-1.oraclecloud.com",
      "objectstorage.eu-milan-1.oraclecloud.com",
      "objectstorage.ap-osaka-1.oraclecloud.com",
      "objectstorage.ap-tokyo-1.oraclecloud.com",
      "objectstorage.mx-queretaro-1.oraclecloud.com",
      "objectstorage.mx-monterrey-1.oraclecloud.com",
      "objectstorage.eu-amsterdam-1.oraclecloud.com",
      "objectstorage.me-riyadh-1.oraclecloud.com",
      "objectstorage.me-jeddah-1.oraclecloud.com",
      "objectstorage.eu-jovanovac-1.oraclecloud.com",
      "objectstorage.ap-singapore-1.oraclecloud.com",
      "objectstorage.ap-singapore-2.oraclecloud.com",
      "objectstorage.af-johannesburg-1.oraclecloud.com",
      "objectstorage.ap-seoul-1.oraclecloud.com",
      "objectstorage.ap-chuncheon-1.oraclecloud.com",
      "objectstorage.eu-madrid-1.oraclecloud.com",
      "objectstorage.eu-stockholm-1.oraclecloud.com",
      "objectstorage.eu-zurich-1.oraclecloud.com",
      "objectstorage.me-abudhabi-1.oraclecloud.com",
      "objectstorage.me-dubai-1.oraclecloud.com",
      "objectstorage.uk-london-1.oraclecloud.com",
      "objectstorage.uk-cardiff-1.oraclecloud.com",
      "objectstorage.us-ashburn-1.oraclecloud.com",
      "objectstorage.us-chicago-1.oraclecloud.com",
      "objectstorage.us-phoenix-1.oraclecloud.com",
      "objectstorage.us-sanjose-1.oraclecloud.com",
  ]

  lowest_latency = find_lowest_latency(domains)

  if lowest_latency:
    print("Lowest latency domains (top 3):")
    for domain, latency in lowest_latency[:3]:
      print(f"  {domain}: {latency:.2f} ms") # Format to two decimal places
  else:
    print("Could not determine lowest latency domains.")

if __name__ == "__main__":
  main()
