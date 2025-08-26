package main

import (
	"github.com/BurntSushi/toml"
)

type Config struct {
	Domain struct {
		Length      int    `toml:"length"`
		Suffix      string `toml:"suffix"`
		Pattern     string `toml:"pattern"`
		RegexFilter string `toml:"regex_filter"`
	} `toml:"domain"`

	Scanner struct {
		Delay         int  `toml:"delay"`
		Workers       int  `toml:"workers"`
		ShowRegistered bool `toml:"show_registered"`
		Methods       struct {
			DNSCheck  bool `toml:"dns_check"`
			WHOISCheck bool `toml:"whois_check"`
			SSLCheck  bool `toml:"ssl_check"`
			HTTPCheck bool `toml:"http_check"`
		} `toml:"methods"`
	} `toml:"scanner"`

	Output struct {
		AvailableFile    string `toml:"available_file"`
		RegisteredFile   string `toml:"registered_file"`
		SpecialStatusFile string `toml:"special_status_file"`
		OutputDir        string `toml:"output_dir"`
		Verbose          bool   `toml:"verbose"`
	} `toml:"output"`
}

func loadConfig(configPath string) (*Config, error) {
	config := &Config{}
	if _, err := toml.DecodeFile(configPath, config); err != nil {
		return nil, err
	}
	
	// Set default values if not specified in config
	if config.Domain.Length == 0 {
		config.Domain.Length = 3
	}
	
	if config.Domain.Suffix == "" {
		config.Domain.Suffix = ".li"
	}
	
	if config.Domain.Pattern == "" {
		config.Domain.Pattern = "D"
	}
	
	if config.Scanner.Delay == 0 {
		config.Scanner.Delay = 1000
	}
	
	if config.Scanner.Workers == 0 {
		config.Scanner.Workers = 10
	}
	
	// Set default values for scanner methods
	if !config.Scanner.Methods.DNSCheck && !config.Scanner.Methods.WHOISCheck && 
	   !config.Scanner.Methods.SSLCheck && !config.Scanner.Methods.HTTPCheck {
		config.Scanner.Methods.DNSCheck = true
		config.Scanner.Methods.WHOISCheck = true
		config.Scanner.Methods.SSLCheck = true
		config.Scanner.Methods.HTTPCheck = false // Disabled by default
	}
	
	if config.Output.AvailableFile == "" {
		config.Output.AvailableFile = "available_domains_{pattern}_{length}_{suffix}.txt"
	}
	
	if config.Output.RegisteredFile == "" {
		config.Output.RegisteredFile = "registered_domains_{pattern}_{length}_{suffix}.txt"
	}
	
	if config.Output.SpecialStatusFile == "" {
		config.Output.SpecialStatusFile = "special_status_domains_{pattern}_{length}_{suffix}.txt"
	}
	
	if config.Output.OutputDir == "" {
		config.Output.OutputDir = "."
	}
	
	return config, nil
}