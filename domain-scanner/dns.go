package main

import (
	"net"
)

func checkDNSRecords(domain string) ([]string, error) {
	var signatures []string

	// 1. Check DNS NS records
	nsRecords, err := net.LookupNS(domain)
	if err == nil && len(nsRecords) > 0 {
		signatures = append(signatures, "DNS_NS")
	}

	// 2. Check DNS A records
	ipRecords, err := net.LookupIP(domain)
	if err == nil && len(ipRecords) > 0 {
		signatures = append(signatures, "DNS_A")
	}

	// 3. Check DNS MX records
	mxRecords, err := net.LookupMX(domain)
	if err == nil && len(mxRecords) > 0 {
		signatures = append(signatures, "DNS_MX")
	}

	// 4. Check DNS TXT records
	txtRecords, err := net.LookupTXT(domain)
	if err == nil && len(txtRecords) > 0 {
		signatures = append(signatures, "DNS_TXT")
	}

	// 5. Check DNS CNAME records
	cnameRecord, err := net.LookupCNAME(domain)
	if err == nil && cnameRecord != "" && cnameRecord != domain+"." {
		signatures = append(signatures, "DNS_CNAME")
	}

	return signatures, nil
}