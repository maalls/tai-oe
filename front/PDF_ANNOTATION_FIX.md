# PDF Annotation Positioning Fix Plan

## Problem

When the user resizes the window, annotations shift position relative to the PDF content. For example:

- Draw circle around text at position (x, y)
- Resize window wider/narrower
- Same circle is now at different position relative to the text

## Root Cause

The browser's built-in PDF viewer inside the iframe repositions the PDF document on resize:

- PDF viewer centers PDFs with margins based on available width
- These margins change on resize
- Canvas is absolutely positioned and resizes as percentage
- Canvas scaling doesn't match PDF viewer's internal repositioning

Example:

- Initial: Container 1000px, PDF centered with 50px margins (900px PDF visible)
- After resize: Container 1200px, PDF centered with 70px margins (1060px PDF visible)
- Both PDF and canvas resize, but with different effective areas

## Solutions Attempted

1. **Offset Detection** - Query iframe DOM for PDF viewer position
   - Issue: Cross-origin restrictions make this unreliable
   - Attempted with `detectPdfOffset()` function - didn't work

2. **Pure Normalized Coordinates** - Store 0-1 coordinates scaled to canvas
   - Issue: Works if PDF margins stay constant, but they change on resize
   - Current implementation uses this - still positioning shifts

3. **Store Canvas Dimensions** - Add storedCanvasWidth/Height to segments
   - Issue: Doesn't account for PDF viewer's internal repositioning
   - Just a fallback, not a real fix

## Solution Currently Attempted

Store PDF page dimensions (width/height) from PDF metadata using pdfjs-dist:

- Get actual PDF page size from first page
- Store with each annotation
- On redraw, potentially use PDF page dims instead of canvas dims

Problem: Still doesn't fix the relative positioning because:

- PDF viewer controls where PDF appears in container
- Even with PDF page dimensions, we need to know where in the container the PDF starts
- Without cross-origin iframe access, can't reliably get PDF viewer's margins/position

## Real Solution Needed

One of these approaches:

### Option A: Use Fixed Viewport

- Disable PDF responsive resizing
- Lock PDF viewer at specific size
- Annotations stay positioned since no internal repositioning happens
- Tradeoff: Less responsive UI

### Option B: Track Iframe Scroll/Transform

- Monitor iframe.contentWindow.scrollX/Y
- Monitor transform values on PDF viewer container
- Apply these offsets when drawing and redrawing
- Requires cross-origin access (may not work)

### Option C: Switch to Embedded PDF Processing

- Use pdfjs-dist to render PDF ourselves on canvas
- Full control over positioning and zoom
- Tradeoff: More complex, rendering overhead

### Option D: Server-Side Annotations

- Store annotations with PDF page number + coordinates
- Backend applies annotations when generating PDF
- Clients just view pre-annotated PDFs
- Tradeoff: Loss of live annotation capability

### Option E: Accept the Positioning Issue (Temporary)

- Document that zooming/resizing may shift annotations
- Implement "snap to position" or "refresh" button
- Let users re-draw/adjust annotations after resize
- Tradeoff: Bad UX but functional

## Recommended Approach

Implement **Option A: Fixed Viewport** as interim solution:

- Set PDF viewer to specific zoom level (already using zoom=page-width)
- Disable browser zoom in iframe
- Disable responsive resizing in PDF viewer CSS
- This prevents internal repositioning that causes the shifts

## Implementation Steps

1. Add CSS to iframe to prevent scaling
2. Lock zoom with URL parameters or CSS
3. Test if annotations stay positioned on resize
4. Add warning if user tries to zoom

## Current Code State

- `PdfAnnotator.vue` has extended logging for debugging
- `loadPdfDimensions()` retrieves PDF page size
- Console logs show canvas, iframe, and annotation coordinates
- `drawLine()` captures both canvas and PDF dimensions
- `redrawAnnotations()` scales normalized coords to current canvas size

## Next Steps

1. Run dev server and test with extensive logging
2. Draw annotation and resize window
3. Check console logs to see:
   - Canvas dimensions before/after resize
   - Iframe position before/after resize
   - Annotation pixel positions (expected vs actual)
4. Determine which component is shifting
5. Implement appropriate fix based on findings
