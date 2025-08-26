package main

import (
	"crypto/tls"
	"flag"
	"fmt"
	"net"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/likexian/whois"
)

// Create a global variable to hold the config
var config *Config

type DomainResult struct {
	Domain       string
	Available    bool
	Error        error
	Signatures   []string
	SpecialStatus string
}

func checkDomainSignatures(domain string) ([]string, error) {
	var signatures []string

	// 1. Check DNS records (if enabled)
	if config == nil || config.Scanner.Methods.DNSCheck {
		dnsSignatures, err := checkDNSRecords(domain)
		if err == nil {
			signatures = append(signatures, dnsSignatures...)
		}
	}

	// 2. Check WHOIS information with retry (if enabled)
	if config == nil || config.Scanner.Methods.WHOISCheck {
		var whoisResult string
		maxRetries := 3
		for i := 0; i < maxRetries; i++ {
			result, err := whois.Whois(domain)
			if err == nil {
				whoisResult = result
				break
			}
			if i < maxRetries-1 {
				time.Sleep(time.Second * 2) // Wait 2 seconds before retry
			}
		}

		if whoisResult != "" {
			// Convert WHOIS response to lowercase for case-insensitive matching
			result := strings.ToLower(whoisResult)

			// Check for registration indicators
			registeredIndicators := []string{
				"registrar:",
				"registrant:",
				"creation date:",
				"created:",
				"updated date:",
				"updated:",
				"expiration date:",
				"expires:",
				"name server:",
				"nserver:",
				"nameserver:",
				"status: active",
				"status: client",
				"status: ok",
				"status: locked",
				"domain name:",
				"domain:",
			}

			for _, indicator := range registeredIndicators {
				if strings.Contains(result, indicator) {
					signatures = append(signatures, "WHOIS")
					break
				}
			}

			// Check for reserved domain indicators
			reservedIndicators := []string{
				"status: reserved",
				"status: restricted",
				"status: blocked",
				"status: prohibited",
				"status: reserved for registry",
				"status: reserved for registrar",
				"status: reserved for registry operator",
				"status: reserved for future use",
				"status: not available for registration",
				"status: not available for general registration",
				"status: reserved for special purposes",
				"status: reserved for government use",
				"status: reserved for educational institutions",
				"status: reserved for non-profit organizations",
				"domain reserved",
				"this domain is reserved",
				"reserved domain",
			}

			for _, indicator := range reservedIndicators {
				if strings.Contains(result, indicator) {
					signatures = append(signatures, "RESERVED")
					break
				}
			}
		}
	}

	// 3. Check SSL certificate with timeout (if enabled)
	if config == nil || config.Scanner.Methods.SSLCheck {
		conn, err := tls.DialWithDialer(&net.Dialer{
			Timeout: 5 * time.Second,
		}, "tcp", domain+":443", &tls.Config{
			InsecureSkipVerify: true,
		})
		if err == nil {
			defer func() {
				_ = conn.Close()
			}()
			state := conn.ConnectionState()
			if len(state.PeerCertificates) > 0 {
				signatures = append(signatures, "SSL")
			}
		}
	}

	return signatures, nil
}

func checkDomainAvailability(domain string) (bool, error) {
	signatures, err := checkDomainSignatures(domain)
	if err != nil {
		return false, err
	}

	// If domain is reserved, it's not available
	for _, sig := range signatures {
		if sig == "RESERVED" {
			return false, nil
		}
	}

	// If any other signature is found, domain is registered
	if len(signatures) > 0 {
		return false, nil
	}

	// If no signatures found, check WHOIS as final verification with retry
	maxRetries := 3
	for i := 0; i < maxRetries; i++ {
		result, err := whois.Whois(domain)
		if err == nil {
			// Convert WHOIS response to lowercase for case-insensitive matching
			result = strings.ToLower(result)

			// Check for indicators that domain is definitely available
			availableIndicators := []string{
				"no match for",
				"not found",
				"no data found",
				"no entries found",
				"domain not found",
				"no object found",
				"no matching record",
				"status: free",
				"status: available",
				"available for registration",
				"this domain is available",
				"domain is available",
				"domain available",
			}

			for _, indicator := range availableIndicators {
				if strings.Contains(result, indicator) {
					return true, nil
				}
			}
			
			// Check for registration indicators as a secondary check
			registeredIndicators := []string{
				"registrar:",
				"registrant:",
				"creation date:",
				"created:",
				"updated date:",
				"updated:",
				"expiration date:",
				"expires:",
				"name server:",
				"nserver:",
				"nameserver:",
				"status: active",
				"status: client",
				"status: ok",
				"status: locked",
				"status: connect",  // Connect状态被视为已注册状态
				"domain name:",
				"domain:",
			}
			
			for _, indicator := range registeredIndicators {
				if strings.Contains(result, indicator) {
					return false, nil
				}
			}
			
			// Check for special status indicators
			specialStatusIndicators := []string{
				"status: redemptionperiod",
				"status: pendingdelete",
				"status: hold",
				"status: inactive",
				"status: suspended",
				"status: reserved",
				"status: quarantined",
				// "status: connect",  // Connect状态不被视为特殊状态，但被视为已注册状态
				"status: pending",
				"status: transfer",
				"status: grace",
				"status: autorenewperiod",
				"status: redemption",
				"status: expire",
			}
			
			for _, indicator := range specialStatusIndicators {
				if strings.Contains(result, indicator) {
					return false, nil
				}
			}
			break
		}
		if i < maxRetries-1 {
			time.Sleep(time.Second * 2) // Wait 2 seconds before retry
		}
	}

	// If we can't determine the status, assume the domain is available
	return true, nil
}

func generateDomains(length int, suffix string, pattern string, regexFilter string) []string {
	var domains []string
	letters := "abcdefghijklmnopqrstuvwxyz"
	numbers := "0123456789"

	// Compile regex if provided
	var regex *regexp.Regexp
	var err error
	if regexFilter != "" {
		regex, err = regexp.Compile(regexFilter)
		if err != nil {
			fmt.Printf("Invalid regex pattern: %v\n", err)
			os.Exit(1)
		}
	}

	switch pattern {
	case "d": // Pure numbers
		generateCombinations(&domains, "", numbers, length, suffix, regex)
	case "D": // Pure letters
		generateCombinations(&domains, "", letters, length, suffix, regex)
	case "a": // Alphanumeric
		generateCombinations(&domains, "", letters+numbers, length, suffix, regex)
	default:
		fmt.Println("Invalid pattern. Use -d for numbers, -D for letters, -a for alphanumeric")
		os.Exit(1)
	}

	return domains
}

func generateCombinations(domains *[]string, current string, charset string, length int, suffix string, regex *regexp.Regexp) {
	if len(current) == length {
		domain := current + suffix
		// Apply regex filter if provided
		if regex == nil || regex.MatchString(domain) {
			*domains = append(*domains, domain)
		}
		return
	}

	for _, c := range charset {
		generateCombinations(domains, current+string(c), charset, length, suffix, regex)
	}
}

func worker(id int, jobs <-chan string, results chan<- DomainResult, delay time.Duration) {
	for domain := range jobs {
		available, err := checkDomainAvailability(domain)
		signatures, errSig := checkDomainSignatures(domain)
		if errSig != nil {
			// Log signature check error but continue with domain availability check
			fmt.Printf("Warning: signature check failed for %s: %v\n", domain, errSig)
		}
		
		// Check for special status
		specialStatus := ""
		if !available {
			// Get WHOIS result to check for special status
			whoisResult, whoisErr := whois.Whois(domain)
			if whoisErr == nil {
				isSpecial, status := checkSpecialStatus(whoisResult)
				if isSpecial {
					specialStatus = status
				}
			}
		}
		
		results <- DomainResult{
			Domain:        domain,
			Available:     available,
			Error:         err,
			Signatures:    signatures,
			SpecialStatus: specialStatus,
		}
		time.Sleep(delay)
	}
}

func printHelp() {
	fmt.Println("Domain Scanner - A tool to check domain availability")
	fmt.Println("\nUsage:")
	fmt.Println("  go run main.go [options]")
	fmt.Println("\nOptions:")
	fmt.Println("  -l int      Domain length (default: 3)")
	fmt.Println("  -s string   Domain suffix (default: .li)")
	fmt.Println("  -p string   Domain pattern:")
	fmt.Println("              d: Pure numbers (e.g., 123.li)")
	fmt.Println("              D: Pure letters (e.g., abc.li)")
	fmt.Println("              a: Alphanumeric (e.g., a1b.li)")
	fmt.Println("  -r string   Regex filter for domain names")
	fmt.Println("  -delay int  Delay between queries in milliseconds (default: 1000)")
	fmt.Println("  -workers int Number of concurrent workers (default: 10)")
	fmt.Println("  -show-registered Show registered domains in output (default: false)")
	fmt.Println("  -config string  Path to config file (default: config.toml)")
	fmt.Println("  -h          Show help information")
	fmt.Println("\nExamples:")
	fmt.Println("  1. Check 3-letter .li domains with 20 workers:")
	fmt.Println("     go run main.go -l 3 -s .li -p D -workers 20")
	fmt.Println("\n  2. Check domains with custom delay and workers:")
	fmt.Println("     go run main.go -l 3 -s .li -p D -delay 500 -workers 15")
	fmt.Println("\n  3. Show both available and registered domains:")
	fmt.Println("     go run main.go -l 3 -s .li -p D -show-registered")
	fmt.Println("\n  4. Use config file:")
	fmt.Println("     go run main.go -config config.toml")
}

func showMOTD() {
	fmt.Println("\033[1;36m") // Cyan color
	fmt.Println("╔════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    Domain Scanner v1.0                     ║")
	fmt.Println("║                                                            ║")
	fmt.Println("║  A powerful tool for checking domain name availability     ║")
	fmt.Println("║                                                            ║")
	fmt.Println("║  Developer: www.ict.run                                    ║")
	fmt.Println("║  GitHub:    https://github.com/xuemian168/domain-scanner   ║")
	fmt.Println("║                                                            ║")
	fmt.Println("║  License:   AGPL-3.0                                       ║")
	fmt.Println("║  Copyright © 2025                                          ║")
	fmt.Println("╚════════════════════════════════════════════════════════════╝")
	fmt.Println("\033[0m") // Reset color
	fmt.Println()
}

func main() {
	// Show MOTD
	showMOTD()

	// Define command line flags
	length := flag.Int("l", 3, "Domain length")
	suffix := flag.String("s", ".li", "Domain suffix")
	pattern := flag.String("p", "D", "Domain pattern (d: numbers, D: letters, a: alphanumeric)")
	regexFilter := flag.String("r", "", "Regex filter for domain names")
	delay := flag.Int("delay", 1000, "Delay between queries in milliseconds")
	workers := flag.Int("workers", 10, "Number of concurrent workers")
	showRegistered := flag.Bool("show-registered", false, "Show registered domains in output")
	configPath := flag.String("config", "", "Path to config file")
	help := flag.Bool("h", false, "Show help information")
	flag.Parse()

	if *help {
		printHelp()
		os.Exit(0)
	}

	// Load config file if specified
	if *configPath != "" {
		var err error
		config, err = loadConfig(*configPath)
		if err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
		
		// Override command line flags with config values
		*length = config.Domain.Length
		*suffix = config.Domain.Suffix
		*pattern = config.Domain.Pattern
		if config.Domain.RegexFilter != "" {
			*regexFilter = config.Domain.RegexFilter
		}
		*delay = config.Scanner.Delay
		*workers = config.Scanner.Workers
		*showRegistered = config.Scanner.ShowRegistered
	}

	// Ensure suffix starts with a dot
	if !strings.HasPrefix(*suffix, ".") {
		*suffix = "." + *suffix
	}

	domains := generateDomains(*length, *suffix, *pattern, *regexFilter)
	availableDomains := []string{}
	registeredDomains := []string{}

	fmt.Printf("Checking %d domains with pattern %s and length %d using %d workers...\n",
		len(domains), *pattern, *length, *workers)
	if *regexFilter != "" {
		fmt.Printf("Using regex filter: %s\n", *regexFilter)
	}

	// Create channels for jobs and results
	jobs := make(chan string, len(domains))
	results := make(chan DomainResult, len(domains))

	// Start workers
	for w := 1; w <= *workers; w++ {
		go worker(w, jobs, results, time.Duration(*delay)*time.Millisecond)
	}

	// Send jobs
	for _, domain := range domains {
		jobs <- domain
	}
	close(jobs)

	// Create a channel for domain status messages
	statusChan := make(chan string, len(domains))

	// Start a goroutine to print status messages
	go func() {
		for msg := range statusChan {
			fmt.Println(msg)
		}
	}()

	// Collect results
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for i := 0; i < len(domains); i++ {
			result := <-results
			progress := fmt.Sprintf("[%d/%d]", i+1, len(domains))
			if result.Error != nil {
				statusChan <- fmt.Sprintf("%s Error checking domain %s: %v", progress, result.Domain, result.Error)
				continue
			}

			// Handle special status domains
			if result.SpecialStatus != "" {
				statusChan <- fmt.Sprintf("%s Domain %s is in SPECIAL STATUS [%s]", progress, result.Domain, result.SpecialStatus)
				addSpecialStatusDomain(result.Domain, result.SpecialStatus)
			} else if result.Available {
				statusChan <- fmt.Sprintf("%s Domain %s is AVAILABLE!", progress, result.Domain)
				availableDomains = append(availableDomains, result.Domain)
			} else if *showRegistered {
				sigStr := strings.Join(result.Signatures, ", ")
				statusChan <- fmt.Sprintf("%s Domain %s is REGISTERED [%s]", progress, result.Domain, sigStr)
				registeredDomains = append(registeredDomains, result.Domain)
			}
		}
		close(statusChan)
	}()
	wg.Wait()

	// Save available domains to file
	availableFile := fmt.Sprintf("available_domains_%s_%d_%s.txt", *pattern, *length, strings.TrimPrefix(*suffix, "."))
	if config != nil && config.Output.AvailableFile != "" {
		availableFile = strings.Replace(config.Output.AvailableFile, "{pattern}", *pattern, -1)
		availableFile = strings.Replace(availableFile, "{length}", fmt.Sprintf("%d", *length), -1)
		availableFile = strings.Replace(availableFile, "{suffix}", strings.TrimPrefix(*suffix, "."), -1)
	}
	
	// Create output directory if specified in config
	if config != nil && config.Output.OutputDir != "" && config.Output.OutputDir != "." {
		availableFile = config.Output.OutputDir + "/" + availableFile
		// Create directory if it doesn't exist
		if err := os.MkdirAll(config.Output.OutputDir, 0755); err != nil {
			fmt.Printf("Error creating output directory: %v\n", err)
			os.Exit(1)
		}
	}
	
	file, err := os.Create(availableFile)
	if err != nil {
		fmt.Printf("Error creating output file: %v\n", err)
		os.Exit(1)
	}
	defer func() {
		_ = file.Close()
	}()

	for _, domain := range availableDomains {
		_, err := file.WriteString(domain + "\n")
		if err != nil {
			fmt.Printf("Error writing to file: %v\n", err)
			os.Exit(1)
		}
	}

	// Save registered domains to file only if show-registered is true
	registeredFile := fmt.Sprintf("registered_domains_%s_%d_%s.txt", *pattern, *length, strings.TrimPrefix(*suffix, "."))
	if *showRegistered {
		if config != nil && config.Output.RegisteredFile != "" {
			registeredFile = strings.Replace(config.Output.RegisteredFile, "{pattern}", *pattern, -1)
			registeredFile = strings.Replace(registeredFile, "{length}", fmt.Sprintf("%d", *length), -1)
			registeredFile = strings.Replace(registeredFile, "{suffix}", strings.TrimPrefix(*suffix, "."), -1)
		}
		
		// Use output directory if specified in config
		if config != nil && config.Output.OutputDir != "" && config.Output.OutputDir != "." {
			registeredFile = config.Output.OutputDir + "/" + registeredFile
		}
		
		regFile, err := os.Create(registeredFile)
		if err != nil {
			fmt.Printf("Error creating registered domains file: %v\n", err)
			os.Exit(1)
		}
		defer func() {
			_ = regFile.Close()
		}()

		for _, domain := range registeredDomains {
			_, err := regFile.WriteString(domain + "\n")
			if err != nil {
				fmt.Printf("Error writing to registered domains file: %v\n", err)
				os.Exit(1)
			}
		}
	}
	
	// Save special status domains to file
	err = saveSpecialStatusDomainsToFile(config, *pattern, *length, *suffix)
	if err != nil {
		fmt.Printf("Error saving special status domains: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("\n\nResults saved to:\n")
	fmt.Printf("- Available domains: %s\n", availableFile)
	if *showRegistered {
		fmt.Printf("- Registered domains: %s\n", registeredFile)
	}
	if len(SpecialStatusDomains) > 0 {
		// Print special status domains file path
		specialStatusFile := fmt.Sprintf("special_status_domains_%s_%d_%s.txt", *pattern, *length, strings.TrimPrefix(*suffix, "."))
		if config != nil && config.Output.SpecialStatusFile != "" {
			specialStatusFile = strings.Replace(config.Output.SpecialStatusFile, "{pattern}", *pattern, -1)
			specialStatusFile = strings.Replace(specialStatusFile, "{length}", fmt.Sprintf("%d", *length), -1)
			specialStatusFile = strings.Replace(specialStatusFile, "{suffix}", strings.TrimPrefix(*suffix, "."), -1)
		}
		
		// Use output directory if specified in config
		if config != nil && config.Output.OutputDir != "" && config.Output.OutputDir != "." {
			specialStatusFile = config.Output.OutputDir + "/" + specialStatusFile
		}
		fmt.Printf("- Special status domains: %s\n", specialStatusFile)
	}
	fmt.Printf("\nSummary:\n")
	fmt.Printf("- Total domains checked: %d\n", len(domains))
	fmt.Printf("- Available domains: %d\n", len(availableDomains))
	if *showRegistered {
		fmt.Printf("- Registered domains: %d\n", len(registeredDomains))
	}
	if len(SpecialStatusDomains) > 0 {
		fmt.Printf("- Special status domains: %d\n", len(SpecialStatusDomains))
	}
}
