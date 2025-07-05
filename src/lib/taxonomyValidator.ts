
export interface TaxonomyValidationResult {
  isValid: boolean;
  message: string;
  missingFiles: string[];
  foundFiles: string[];
  debugInfo?: {
    totalFiles: number;
    folderStructure: string[];
    detectedType: 'EBA_v4' | 'Traditional_XBRL' | 'Unknown';
  };
}

export const validateTaxonomyZip = async (file: File): Promise<TaxonomyValidationResult> => {
  // Check if it's a ZIP file
  if (!file.name.toLowerCase().endsWith('.zip')) {
    return {
      isValid: false,
      message: "File must be a ZIP archive",
      missingFiles: [],
      foundFiles: []
    };
  }

  try {
    // Import JSZip dynamically
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();
    const zipContent = await zip.loadAsync(file);
    
    const allFiles = Object.keys(zipContent.files);
    const files = allFiles.filter(filename => !zipContent.files[filename].dir);
    const folders = allFiles.filter(filename => zipContent.files[filename].dir);
    
    console.log('🔍 Taxonomy ZIP Analysis:', {
      totalFiles: files.length,
      folders: folders,
      sampleFiles: files.slice(0, 10)
    });

    // Detect EBA v4.0 Architecture v2.0 structure
    const hasEBAFolders = folders.some(folder => 
      folder.includes('mod/') || folder.includes('val/') || 
      folder.includes('lab/') || folder.includes('xsd/')
    );

    const hasEBAFiles = files.some(file => 
      file.includes('/mod/') || file.includes('/val/') || 
      file.includes('/lab/') || file.includes('/xsd/')
    );

    // EBA-specific patterns
    const ebaPatterns = [
      { pattern: /\.xsd$/i, description: "XML Schema files (.xsd)" },
      { pattern: /(labels?|lab)\.xml$/i, description: "Label linkbase files" },
      { pattern: /(presentation|pre)\.xml$/i, description: "Presentation linkbase files" },
      { pattern: /(calculation|cal)\.xml$/i, description: "Calculation linkbase files" },
      { pattern: /(definition|def)\.xml$/i, description: "Definition linkbase files" },
      { pattern: /entry.*\.xml$/i, description: "Entry point files" }
    ];

    // Traditional XBRL patterns (more restrictive)
    const traditionalPatterns = [
      { pattern: /\.xsd$/i, description: "XML Schema files (.xsd)" },
      { pattern: /_(lab|pre|cal|def)\.xml$/i, description: "Traditional linkbase files" }
    ];

    let detectedType: 'EBA_v4' | 'Traditional_XBRL' | 'Unknown' = 'Unknown';
    let patternsToCheck = traditionalPatterns;

    // Determine taxonomy type and use appropriate patterns
    if (hasEBAFolders || hasEBAFiles) {
      detectedType = 'EBA_v4';
      patternsToCheck = ebaPatterns;
      console.log('✅ Detected EBA Taxonomy v4.0 structure');
    } else {
      // Check for traditional XBRL patterns
      const hasTraditionalPattern = files.some(file => /_(lab|pre|cal|def)\.xml$/i.test(file));
      if (hasTraditionalPattern) {
        detectedType = 'Traditional_XBRL';
        patternsToCheck = traditionalPatterns;
        console.log('✅ Detected Traditional XBRL taxonomy structure');
      }
    }

    const missingTypes: string[] = [];
    const presentTypes: string[] = [];
    
    // Check for required patterns based on detected type
    for (const { pattern, description } of patternsToCheck) {
      const hasPattern = files.some(file => pattern.test(file));
      if (hasPattern) {
        presentTypes.push(description);
      } else {
        missingTypes.push(description);
      }
    }

    // For EBA taxonomies, be more lenient - require at least XSD and some linkbase files
    if (detectedType === 'EBA_v4') {
      const hasXSD = files.some(file => /\.xsd$/i.test(file));
      const hasAnyLinkbase = files.some(file => 
        /\.(xml)$/i.test(file) && 
        (file.includes('lab') || file.includes('pre') || file.includes('cal') || file.includes('def') ||
         file.includes('labels') || file.includes('presentation') || file.includes('calculation') || file.includes('definition'))
      );

      if (hasXSD && hasAnyLinkbase) {
        return {
          isValid: true,
          message: `✅ Valid EBA Taxonomy v4.0 package detected with ${files.length} files`,
          missingFiles: [],
          foundFiles: presentTypes,
          debugInfo: {
            totalFiles: files.length,
            folderStructure: folders,
            detectedType
          }
        };
      } else {
        return {
          isValid: false,
          message: `❌ EBA Taxonomy v4.0 package incomplete - missing ${!hasXSD ? 'XSD files' : 'linkbase files'}`,
          missingFiles: !hasXSD ? ['XML Schema files'] : ['Linkbase files'],
          foundFiles: presentTypes,
          debugInfo: {
            totalFiles: files.length,
            folderStructure: folders,
            detectedType
          }
        };
      }
    }

    // For traditional XBRL, use stricter validation
    if (detectedType === 'Traditional_XBRL') {
      if (missingTypes.length === 0) {
        return {
          isValid: true,
          message: `✅ Valid Traditional XBRL taxonomy package found with ${files.length} files`,
          missingFiles: [],
          foundFiles: presentTypes,
          debugInfo: {
            totalFiles: files.length,
            folderStructure: folders,
            detectedType
          }
        };
      } else {
        return {
          isValid: false,
          message: `❌ Incomplete Traditional XBRL taxonomy package`,
          missingFiles: missingTypes,
          foundFiles: presentTypes,
          debugInfo: {
            totalFiles: files.length,
            folderStructure: folders,
            detectedType
          }
        };
      }
    }

    // Unknown type - try to be helpful
    const hasAnyXSD = files.some(file => /\.xsd$/i.test(file));
    const hasAnyXML = files.some(file => /\.xml$/i.test(file));

    if (hasAnyXSD && hasAnyXML) {
      return {
        isValid: true,
        message: `⚠️ Taxonomy package accepted (${files.length} files) - structure not fully recognized but contains XSD and XML files`,
        missingFiles: [],
        foundFiles: ['XML Schema files', 'XML files'],
        debugInfo: {
          totalFiles: files.length,
          folderStructure: folders,
          detectedType: 'Unknown'
        }
      };
    } else {
      return {
        isValid: false,
        message: `❌ Invalid taxonomy package - no recognizable XBRL structure found`,
        missingFiles: ['XML Schema files', 'Linkbase files'],
        foundFiles: [],
        debugInfo: {
          totalFiles: files.length,
          folderStructure: folders,
          detectedType: 'Unknown'
        }
      };
    }
    
  } catch (error) {
    console.error('❌ Error validating taxonomy ZIP:', error);
    return {
      isValid: false,
      message: "❌ Could not read ZIP file - file may be corrupted",
      missingFiles: [],
      foundFiles: []
    };
  }
};
