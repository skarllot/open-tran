%module tran
%{
#include "storage.h"
%}

storage_t *storage_create (const char *lang);
void storage_destroy (storage_t *storage);

void storage_add (storage_t *storage, const char *text, int location_id);
void storage_read (storage_t *storage, const char *dbname);
suggestion_t *storage_suggest (storage_t *storage, const char *text);

int suggestion_get_count (suggestion_t *suggestion);
unsigned suggestion_get_id (suggestion_t *suggestion, int idx);
int suggestion_get_value (suggestion_t *suggestion, int idx);
void suggestion_destroy (suggestion_t *suggestion);
