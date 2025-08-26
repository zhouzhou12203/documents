package main

import (
	"fmt"
	"os"
	"strings"
)

// SpecialStatus 定义特殊状态域名的结构
type SpecialStatus struct {
	Domain string
	Status string
}

// SpecialStatusDomains 存储特殊状态域名的列表
var SpecialStatusDomains []SpecialStatus

// checkSpecialStatus 检查域名是否处于特殊状态（如redemptionPeriod）
// 注意：Connect状态不被视为特殊状态，因此不包含在内
func checkSpecialStatus(whoisResult string) (bool, string) {
	// 转换为小写以进行不区分大小写的匹配
	result := strings.ToLower(whoisResult)
	
	// 定义特殊状态指示器（不包括Connect状态）
	specialStatusIndicators := map[string]string{
		"status: redemptionperiod":  "Redemption Period",
		"status: pendingdelete":     "Pending Delete",
		"status: hold":              "Hold",
		"status: inactive":          "Inactive",
		"status: suspended":         "Suspended",
		"status: reserved":          "Reserved",
		"status: quarantined":       "Quarantined",
		// "status: connect":        "Connect",  // Connect状态不被视为特殊状态
		"status: pending":           "Pending Registration",
		"status: transfer":          "Transfer Pending",
		"status: grace":             "Grace Period",
		"status: autorenewperiod":   "Auto-Renew Period",
		"status: redemption":        "Redemption Period",  // 另一种写法
		"status: expire":            "Expired",
	}
	
	// 检查是否存在特殊状态
	for indicator, status := range specialStatusIndicators {
		if strings.Contains(result, indicator) {
			return true, status
		}
	}
	
	// 单独检查Connect状态，但不将其视为特殊状态
	if strings.Contains(result, "status: connect") {
		return false, ""  // Connect状态不被视为特殊状态
	}
	
	return false, ""
}

// addSpecialStatusDomain 添加特殊状态域名到列表
func addSpecialStatusDomain(domain, status string) {
	SpecialStatusDomains = append(SpecialStatusDomains, SpecialStatus{
		Domain: domain,
		Status: status,
	})
}

// saveSpecialStatusDomainsToFile 保存特殊状态域名到文件
func saveSpecialStatusDomainsToFile(config *Config, pattern string, length int, suffix string) error {
	if len(SpecialStatusDomains) == 0 {
		return nil // 没有特殊状态域名，无需保存
	}
	
	// 构建文件名
	specialStatusFile := fmt.Sprintf("special_status_domains_%s_%d_%s.txt", pattern, length, strings.TrimPrefix(suffix, "."))
	if config != nil && config.Output.SpecialStatusFile != "" {
		specialStatusFile = strings.Replace(config.Output.SpecialStatusFile, "{pattern}", pattern, -1)
		specialStatusFile = strings.Replace(specialStatusFile, "{length}", fmt.Sprintf("%d", length), -1)
		specialStatusFile = strings.Replace(specialStatusFile, "{suffix}", strings.TrimPrefix(suffix, "."), -1)
	}
	
	// 使用输出目录（如果在配置中指定）
	if config != nil && config.Output.OutputDir != "" && config.Output.OutputDir != "." {
		specialStatusFile = config.Output.OutputDir + "/" + specialStatusFile
	}
	
	// 创建文件
	file, err := os.Create(specialStatusFile)
	if err != nil {
		return fmt.Errorf("error creating special status domains file: %v", err)
	}
	defer func() {
		_ = file.Close()
	}()
	
	// 写入特殊状态域名
	for _, domain := range SpecialStatusDomains {
		_, err := file.WriteString(fmt.Sprintf("%s\t%s\n", domain.Domain, domain.Status))
		if err != nil {
			return fmt.Errorf("error writing to special status domains file: %v", err)
		}
	}
	
	fmt.Printf("- Special status domains: %s\n", specialStatusFile)
	return nil
}